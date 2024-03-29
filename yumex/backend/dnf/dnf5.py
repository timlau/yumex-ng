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

from typing import Iterable

import libdnf5.base as dnf
from libdnf5.rpm import PackageQuery, Package  # noqa: F401
from libdnf5.repo import RepoQuery, Repo  # noqa : F401
from libdnf5.common import (
    QueryCmp_NEQ,
    QueryCmp_NOT_IGLOB,
    QueryCmp_ICONTAINS,
    QueryCmp_IGLOB,
)

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


class UpdateInfo:
    """Wrapper class for dnf update advisories on a given po."""

    UPDINFO_MAIN = ["id", "title", "type", "description"]

    def __init__(self, po):
        self.po = po

    @staticmethod
    def advisories_iter(po):
        pass

    def advisories_list(self):
        """list containing advisory information."""
        results = []
        for adv in self.advisories_iter(self.po):
            e = {}
            # main fields
            for field in UpdateInfo.UPDINFO_MAIN:
                e[field] = getattr(adv, field)
            dt = getattr(adv, "updated")
            e["updated"] = dt.isoformat(" ")
            # manage packages references
            refs = []
            for ref in adv.references:
                ref_tuple = [ref.type, ref.id, ref.title, ref.url]
                refs.append(ref_tuple)
            e["references"] = refs
            results.append(e)
        return results


class Backend(dnf.Base):
    def __init__(self, presenter: Presenter, *args) -> None:
        super().__init__(*args)
        self.presenter: Presenter = presenter
        self.load_config_from_file()
        self.setup()
        self.reset_backend()

    def reset_backend(self) -> None:
        self.repo_sack = self.get_repo_sack()
        self.repo_sack.create_repos_from_system_configuration()
        self.repo_sack.update_and_load_enabled_repos(True)

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

    def _get_yumex_packages(
        self, query: PackageQuery, state=PackageState.AVAILABLE
    ) -> list[YumexPackage]:
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

    def search(
        self, key: str, field: SearchField = SearchField.NAME, limit: int = 1
    ) -> list[YumexPackage]:
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

    def get_packages(self, pkg_filter: PackageFilter) -> list[YumexPackage]:
        match pkg_filter:
            case PackageFilter.AVAILABLE:
                return self._get_yumex_packages(self.available)
            case PackageFilter.INSTALLED:
                return self._get_yumex_packages(self.installed)
            case PackageFilter.UPDATES:
                return self._get_yumex_packages(self.updates, state=PackageState.UPDATE)
            case other:
                raise ValueError(f"Unknown package filter: {other}")

    def get_package_info(self, pkg: YumexPackage, attr: InfoType) -> str | None:
        query = PackageQuery(self)
        if pkg.state == PackageState.AVAILABLE:
            query.filter_available()
        else:
            query.filter_available()
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
                case InfoType.UPDATE_INFO:  # TODO: implement
                    # updinfo = UpdateInfo(dnf_pkg)
                    # value = updinfo.advisories_list()
                    # return value
                    return None
                case other:
                    raise ValueError(f"Unknown package info: {other}")
        else:
            raise ValueError(f"dnf package not found: {pkg}")

    def get_repositories(self) -> list[tuple[str, str, bool]]:
        query = RepoQuery(self)
        query.filter_id("*-source", QueryCmp_NOT_IGLOB)
        query.filter_id("*-debuginfo", QueryCmp_NOT_IGLOB)
        return [(repo.get_id(), repo.get_name(), repo.is_enabled()) for repo in query]

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
