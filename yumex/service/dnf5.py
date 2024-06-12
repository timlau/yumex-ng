import libdnf5 as dnf
from libdnf5.rpm import PackageQuery, Package  # noqa: F401
from libdnf5.repo import RepoQuery  # noqa: F401
from libdnf5.common import QueryCmp_NEQ
from typing import List

def UpdateChecker() -> List[Package]:
    base = dnf.base.Base()
    cache_directory = base.get_config().get_cachedir_option().get_value()
    base.get_config().get_system_cachedir_option().set(cache_directory)

    base.load_config()
    base.setup()

    def reset_backend(base: dnf.base.Base) -> None:
        base.repo_sack = base.get_repo_sack()
        base.repo_sack.create_repos_from_system_configuration()
        base.repo_sack.update_and_load_enabled_repos(True)

    reset_backend(base)

    def get_repo_priority(base: dnf.base.Base, repo_name: str) -> int:
        repos_query = RepoQuery(base)
        for repo in repos_query:
            if repo.get_id() == repo_name:
                return repo.get_priority()
        return 99

    def get_package_repos(base: dnf.base.Base, package_name: str) -> List[str]:
        repos = set()
        query = PackageQuery(base)
        query.filter_name([package_name])
        for pkg in query:
            repos.add(pkg.get_repo_id())
        return list(repos)

    updates = PackageQuery(base)
    updates.filter_upgrades()
    updates.filter_arch(["src"], QueryCmp_NEQ)
    updates.filter_latest_evr()

    updates_list = list(updates)

    latest_versions = {}
    for pkg in updates_list:
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
