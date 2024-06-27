# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2024 Tim Lauridsen

from typing import Iterable, List
from datetime import datetime
from dataclasses import asdict, dataclass
from pathlib import Path

import libdnf5.base as dnf

from libdnf5.rpm import PackageQuery, Package  # noqa: F401
from libdnf5.repo import RepoQuery, RepoCache, Repo  # noqa : F401
from libdnf5.common import QueryCmp_NEQ, QueryCmp_NOT_IGLOB, QueryCmp_ICONTAINS, QueryCmp_IGLOB
from libdnf5.advisory import AdvisoryQuery, Advisory, AdvisoryReference


from yumex.backend.dnf import YumexPackage
from yumex.backend.interface import Presenter
from yumex.utils.enums import SearchField, PackageState, InfoType, PackageFilter

from yumex.utils import log


def create_package(pkg: Package) -> YumexPackage:
    if pkg.is_installed():
        state = PackageState.INSTALLED
        repo = pkg.get_from_repo_id()
    else:
        state = PackageState.AVAILABLE
        repo = pkg.get_repo_id()

    return YumexPackage(
        name=pkg.get_name(),
        arch=pkg.get_arch(),
        epoch=pkg.get_epoch(),
        release=pkg.get_release(),
        version=pkg.get_version(),
        repo=repo,
        description=pkg.get_summary(),
        size=pkg.get_install_size(),
        state=state,
    )


@dataclass
class UpdateInfo:
    id: str
    title: str
    description: str
    type: str
    updated: str
    references: list

    @classmethod
    def from_advisory(cls, advisory: Advisory):
        """make UpdateInfo object from an Advisory"""
        # build list of references
        refs: list[AdvisoryReference] = list(advisory.get_references())
        ref_list = []
        for ref in refs:
            ref_list.append((ref.get_type(), ref.get_id(), ref.get_title(), ref.get_url()))
        return cls(
            id=advisory.get_name(),
            title=advisory.get_title(),
            description=advisory.get_description(),
            type=advisory.get_type(),
            updated=datetime.fromtimestamp(advisory.get_buildtime()).strftime("%Y-%m-%d %H:%M:%S"),
            references=ref_list,
        )

    def as_dict(self):
        """return dataclass as a dict"""
        return asdict(self)


class Backend(dnf.Base):
    def __init__(self, presenter: Presenter, *args) -> None:
        super().__init__(*args)

        # Yumex is run as user, force it to use user cache instead of systems
        # This allows it to refresh the metadata correctly.
        # It already does the same thing in DNF4
        cache_directory = self.get_config().get_cachedir_option().get_value()
        self.get_config().get_system_cachedir_option().set(cache_directory)

        self.presenter: Presenter = presenter
        self.load_config()
        self.setup()
        self.reset_backend()

    def reset_backend(self) -> None:
        self.repo_sack = self.get_repo_sack()
        self.repo_sack.create_repos_from_system_configuration()
        # FIXME: should be cleaned up when dnf5 5.1.x support is not needed
        try:
            self.repo_sack.load_repos()  # dnf5 5.2.0
        except Exception:
            log("repo_sack.load_repos() failed, fallback to update_and_load_enabled_repos")
            self.repo_sack.update_and_load_enabled_repos(True)  # dnf5 5.1.x

    @property
    def installed(self) -> PackageQuery:
        query = PackageQuery(self)
        query.filter_installed()
        return query

    @property
    def available(self) -> PackageQuery:
        query = PackageQuery(self)
        query.filter_available()
        query.filter_arch(["src"], QueryCmp_NEQ)
        query.filter_latest_evr()
        return query

    @property
    def updates(self) -> PackageQuery:
        query = PackageQuery(self)
        query.filter_upgrades()
        query.filter_arch(["src"], QueryCmp_NEQ)
        query.filter_latest_evr()
        return query

    def _get_yumex_packages(self, query: PackageQuery, state=PackageState.AVAILABLE) -> list[YumexPackage]:
        updates = self.updates
        nevra_dict = {}
        for pkg in query:
            ypkg: YumexPackage = create_package(pkg)
            if pkg.is_installed():
                ypkg.set_state(PackageState.INSTALLED)
            if state == PackageState.UPDATE or updates.contains(pkg):
                ypkg.set_state(PackageState.UPDATE)
            if ypkg.nevra not in nevra_dict:
                nevra_dict[ypkg.nevra] = ypkg
            else:
                log(f"Skipping duplicate : {ypkg}")
        return list(nevra_dict.values())

    def search(self, key: str, field: SearchField = SearchField.NAME, limit: int = 1) -> list[YumexPackage]:
        qa = PackageQuery(self)
        qa.filter_available()
        qa.filter_arch(["src"], QueryCmp_NEQ)
        qa.filter_latest_evr(limit=limit)
        qi = PackageQuery(self)
        qi.filter_installed()
        match field:
            case SearchField.NAME:
                if "*" in key:
                    qi.filter_name([key], QueryCmp_IGLOB)
                    qa.filter_name([key], QueryCmp_IGLOB)
                else:
                    qi.filter_name([key], QueryCmp_ICONTAINS)
                    qa.filter_name([key], QueryCmp_ICONTAINS)
            case SearchField.ARCH:
                qa.filter_arch([key])
                qi.filter_arch([key])
            case SearchField.REPO:
                qa.filter_repo_id([key])
                qi.filter_repo_id([key])
            case SearchField.SUMMARY:
                qi.filter_summary([key], QueryCmp_ICONTAINS)
                qa.filter_summary([key], QueryCmp_ICONTAINS)
            case other:
                msg = f"Search field : [{other}] not supported in dnf5 backend"
                log(msg)
                raise ValueError(msg)
        qa.update(qi)
        return self._get_yumex_packages(qa)

    def expire_metadata(self):
        # get the repo cache dir
        cachedir = Path(self.get_config().get_cachedir_option().get_value())
        log(f"DNF5: current cachedir : {cachedir}")
        # interate through the repo cachedir
        for fn in cachedir.iterdir():
            log(f"DNF5: expire repo loacted at {fn}")
            # Setup a RepoCache at the current repo cachedir
            repo_cache = RepoCache(self, fn.as_posix())
            # expire the cache for the current repo
            repo_cache.write_attribute(RepoCache.ATTRIBUTE_EXPIRED)

    def get_repo_priority(self, repo_name: str) -> int:
        """Fetches the priority of a specified repository using DNF5 API."""

        repos_query = RepoQuery(self)

        # Iterate through the repositories to find the one matching the repo_name
        for repo in repos_query:
            if repo.get_id() == repo_name:
                return repo.get_priority()
        else:
            # Return a default value if the repository name was not found
            return 99

    def get_package_repos(self, package_name: str) -> List[str]:
        """Fetches the repositories providing a given package using DNF5 API."""
        repos = set()
        query = PackageQuery(self)
        query.filter_name([package_name])
        for pkg in query:
            repos.add(pkg.get_repo_id())
        return list(repos)

    def get_packages_with_lowest_priority(self, packages: List[YumexPackage]) -> List[YumexPackage]:
        updates_list = list(packages)
        latest_versions = {}
        for pkg in updates_list:
            repos = self.get_package_repos(pkg.name)

            # Get the priority for each repository and store them in a list
            repo_priorities = [self.get_repo_priority(repo) for repo in repos]

            # Find the lowest priority among the repositories
            lowest_priority = min(repo_priorities) if repo_priorities else float("99")

            # Get the priority of the current package's repository
            pkg_repo_priority = self.get_repo_priority(pkg.repo)

            # Check if the priority of pkg.repo matches the lowest priority
            if pkg_repo_priority == lowest_priority:
                if pkg.name in latest_versions:
                    if pkg.evr > latest_versions[pkg.name].evr:
                        latest_versions[pkg.name] = pkg
                else:
                    latest_versions[pkg.name] = pkg

        return list(latest_versions.values())

    def get_packages(self, pkg_filter: PackageFilter) -> list[YumexPackage]:
        match pkg_filter:
            case PackageFilter.AVAILABLE:
                return self._get_yumex_packages(self.available)
            case PackageFilter.INSTALLED:
                return self._get_yumex_packages(self.installed)
            case PackageFilter.UPDATES:
                self.expire_metadata()
                # sync_updates()
                packages = self._get_yumex_packages(self.updates, state=PackageState.UPDATE)
                return self.get_packages_with_lowest_priority(packages)
            case other:
                raise ValueError(f"Unknown package filter: {other}")

    def _get_advisory_info(self, query):
        result = []
        advisories = [adv_pkg.get_advisory() for adv_pkg in AdvisoryQuery(self).get_advisory_packages_sorted(query)]
        for advisory in advisories:
            upd_info = UpdateInfo.from_advisory(advisory)
            result.append(upd_info.as_dict())
        if result:
            return result
        else:
            return None

    def get_package_info(self, pkg: YumexPackage, attr: InfoType) -> str | None:
        query = PackageQuery(self)
        if pkg.state == PackageState.AVAILABLE:
            query.filter_available()
        else:
            query.filter_installed()
        query.filter_nevra([pkg.nevra])
        pkgs = list(query)
        if not pkgs:
            return None
        dnf_pkg = pkgs[0]
        if dnf_pkg:
            match attr:
                case InfoType.DESCRIPTION:
                    return dnf_pkg.get_description()
                case InfoType.FILES:
                    return dnf_pkg.get_files()
                case InfoType.UPDATE_INFO:
                    return self._get_advisory_info(query)
                case other:
                    raise ValueError(f"Unknown package info: {other}")
        else:
            raise ValueError(f"dnf package not found: {pkg}")

    def get_repositories(self) -> list[tuple[str, str, bool, int]]:
        query = RepoQuery(self)
        query.filter_id("*-source", QueryCmp_NOT_IGLOB)
        query.filter_id("*-debuginfo", QueryCmp_NOT_IGLOB)
        return [(repo.get_id(), repo.get_name(), repo.is_enabled(), repo.get_priority()) for repo in query]

    def depsolve(self, pkgs: Iterable[YumexPackage]) -> list[YumexPackage]:
        goal = dnf.Goal(self)
        goal.set_allow_erasing(True)
        nevra_dict = {}
        deps = []
        for pkg in pkgs:
            nevra = pkg.nevra
            nevra_dict[nevra] = pkg
            match pkg.state:
                case PackageState.INSTALLED:
                    goal.add_rpm_remove(nevra)
                    log(f" DNF5: add {nevra} to transaction for removal")
                case PackageState.UPDATE:
                    goal.add_rpm_upgrade(nevra)
                    log(f" DNF5: add {nevra} to transaction for upgrade")
                case PackageState.AVAILABLE:
                    goal.add_rpm_install(nevra)
                    log(f" DNF5: add {nevra} to transaction for installation")
        transaction: dnf.Transaction = goal.resolve()
        problems = transaction.get_problems()
        log(f" DNF5: depsolve completed : {problems}")
        if problems == dnf.GoalProblem_NO_PROBLEM:
            for tspkg in transaction.get_transaction_packages():
                action = tspkg.get_action()
                pkg = create_package(tspkg.get_package())
                if pkg.nevra not in nevra_dict:
                    # do not add replaced packages as dependencies
                    if action == 6:  # TransactionItemAction::REPLACED
                        break
                    log(f" DNF5: adding as dep : {pkg.nevra} ")
                    pkg.is_dep = True
                    deps.append(pkg)
                else:
                    log(f" DNF5: skipping already in transaction : {pkg.nevra} ")
        else:
            log(f" DNF5 depsolve failed with GoalProblem:  {problems}")
            msgs = transaction.get_resolve_logs_as_strings()
            for msg in msgs:
                log(f"  ---> {msg}")
        return deps
