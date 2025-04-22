import logging
from typing import Callable

from yumex.backend.dnf import YumexPackage

logger = logging.getLogger(__name__)


class FilterUpdates:
    def __init__(self, repo_priority: dict[str, int], packages_by_name: Callable) -> None:
        self.packages_by_name: Callable = packages_by_name
        self.repo_prioritiy: dict[str, int] = repo_priority

    def _filter_updates(self, updates: list[YumexPackage]) -> list:
        """Filter updates based on the repository priority"""
        latest_versions = {}
        for pkg in updates:
            repos = self._get_package_repos(pkg)
            repo_priorities = [self.repo_prioritiy[repo] for repo in repos]
            lowest_priority = min(repo_priorities) if repo_priorities else 99
            pkg_repo_priority = self.repo_prioritiy[pkg.repo]

            if pkg_repo_priority == lowest_priority:
                if pkg.name in latest_versions:
                    if pkg.evr > latest_versions[pkg.name].evr:
                        latest_versions[pkg.name] = pkg
                else:
                    latest_versions[pkg.name] = pkg

        return list(latest_versions.values())

    def _get_repo_priority(self, repo_name: str) -> int:
        """Get the priority of a repository"""
        return self.repo_prioritiy[repo_name]

    def _get_package_repos(self, pkg: YumexPackage) -> list[str]:
        repos = set()
        pkgs = self.packages_by_name(pkg)
        for pkg in pkgs:
            repos.add(pkg.repo)
        return list(repos)

    def get_updates(self, updates: list[YumexPackage]) -> list[YumexPackage]:
        """Get a list of updates from the backend"""
        logger.debug(f"Filtering updates by repo priority: {len(updates)}")
        return self._filter_updates(updates)
