import dnf as dnf


def get_repo_priority(base, repo_name: str) -> int:
    """get the priority of a given repo name"""
    repo = base.repos.get(repo_name)
    return repo.priority if repo else 99


def get_package_repos(base, package_name: str) -> list[str]:
    """get the repositories that a give package name exits in"""
    repos: set[str] = set()
    query = base.sack.query().available().filter(name=package_name)
    for pkg in query.run():
        repos.add(pkg.reponame)
    return list(repos)


def get_prioritied_packages(base, updates):
    """Get Prioritized version of updates"""
    latest_versions = {}
    for pkg in updates:
        repos = get_package_repos(base, pkg.name)
        repo_priorities = [get_repo_priority(base, repo) for repo in repos]
        lowest_priority = min(repo_priorities) if repo_priorities else 99
        pkg_repo_priority = get_repo_priority(base, pkg.reponame)

        if pkg_repo_priority == lowest_priority:
            if pkg.name in latest_versions:
                if pkg.evr > latest_versions[pkg.name].evr:
                    latest_versions[pkg.name] = pkg
            else:
                latest_versions[pkg.name] = pkg

    return list(latest_versions.values())


def check_dnf_updates(refresh: bool) -> list[dnf.package.Package]:
    base = dnf.Base()
    try:
        # Read repo config
        base.read_all_repos()
        # refresh repo metadata
        if refresh:
            for repo in base.repos.iter_enabled():
                repo.metadata_expire = 0
                repo.load()
        # setup sack
        base.fill_sack(load_system_repo=True)
        # get updates
        q = base.sack.query()
        updates = q.upgrades().run()
        return get_prioritied_packages(base, updates)

    finally:
        base.close()


if __name__ == "__main__":
    print(check_dnf_updates())
