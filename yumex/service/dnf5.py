from pathlib import Path

import libdnf5 as dnf
from libdnf5.rpm import PackageQuery, Package  # noqa: F401
from libdnf5.repo import RepoQuery, RepoCache  # noqa: F401
from libdnf5.common import QueryCmp_NEQ


def get_repo_priority(base: dnf.base.Base, repo_name: str) -> int:
    repos_query = RepoQuery(base)
    for repo in repos_query:
        if repo.get_id() == repo_name:
            return repo.get_priority()
    return 99


def get_package_repos(base: dnf.base.Base, package_name: str) -> list[str]:
    repos = set()
    query = PackageQuery(base)
    query.filter_name([package_name])
    for pkg in query:
        repos.add(pkg.get_repo_id())
    return list(repos)


def get_prioritied_packages(updates: PackageQuery, base):
    """Get Prioritized version of updates"""
    latest_versions = {}
    for pkg in updates:
        repos = get_package_repos(base, pkg.get_name())
        repo_priorities = [get_repo_priority(base, repo) for repo in repos]
        lowest_priority = min(repo_priorities) if repo_priorities else 99
        pkg_repo_priority = get_repo_priority(base, pkg.get_repo_id())

        if pkg_repo_priority == lowest_priority:
            if pkg.get_name() in latest_versions:
                if pkg.get_evr() > latest_versions[pkg.get_name()].get_evr():
                    latest_versions[pkg.get_name()] = pkg
            else:
                latest_versions[pkg.get_name()] = pkg

    return list(latest_versions.values())


def expire_metadata(base: dnf.base.Base, cachedir):
    # get the repo cache dir
    cachedir = Path(cachedir)
    # interate through the repo cachedir
    for fn in cachedir.iterdir():
        # Setup a RepoCache at the current repo cachedir
        repo_cache = RepoCache(base, fn.as_posix())
        # expire the cache for the current repo
        repo_cache.write_attribute(RepoCache.ATTRIBUTE_EXPIRED)


def check_dnf_updates() -> list[Package]:
    base = dnf.base.Base()
    try:
        # Setup dnf base
        cache_directory = base.get_config().get_cachedir_option().get_value()
        expire_metadata(base, cache_directory)
        base.get_config().get_system_cachedir_option().set(cache_directory)
        base.load_config()
        base.setup()
        # Setup repositories
        base.repo_sack = base.get_repo_sack()
        base.repo_sack.create_repos_from_system_configuration()
        base.repo_sack.update_and_load_enabled_repos(True)
        # Get availble updates
        updates = PackageQuery(base)
        updates.filter_upgrades()
        updates.filter_arch(["src"], QueryCmp_NEQ)
        updates.filter_latest_evr()
        return get_prioritied_packages(updates, base)
    finally:
        del base


if __name__ == "__main__":
    print(check_dnf_updates())
