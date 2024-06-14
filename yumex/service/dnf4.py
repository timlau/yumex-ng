import dnf as dnf
from typing import List, Set

def UpdateChecker() -> List[dnf.package.Package]:
    base = dnf.Base()
    base.read_all_repos()

    def metadata_refresh(base: dnf.Base) -> None:
        for repo in base.repos.iter_enabled():
            repo.metadata_expire = 0
            repo.load()

    def get_repo_priority(repo_name: str) -> int:
        repo = base.repos.get(repo_name)
        return repo.priority if repo else 99

    def get_package_repos(package_name: str) -> List[str]:
        repos: Set[str] = set()
        query = base.sack.query().available().filter(name=package_name)
        for pkg in query.run():
            repos.add(pkg.reponame)
        return list(repos)

    base.fill_sack(load_system_repo=True)
    q = base.sack.query()
    updates = q.upgrades().run()

    metadata_refresh(base)

    latest_versions = {}
    for pkg in updates:
        repos = get_package_repos(pkg.name)
        repo_priorities = [get_repo_priority(repo) for repo in repos]
        lowest_priority = min(repo_priorities) if repo_priorities else 99
        pkg_repo_priority = pkg.repo.priority

        if pkg_repo_priority == lowest_priority:
            if pkg.name in latest_versions:
                if pkg.evr > latest_versions[pkg.name].evr:
                    latest_versions[pkg.name] = pkg
            else:
                latest_versions[pkg.name] = pkg

    return list(latest_versions.values())
