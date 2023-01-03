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
# Copyright (C) 2023  Tim Lauridsen

from time import time
from typing import Union

import dnf
import dnf.yum
import dnf.const
import dnf.conf
import dnf.subject
import hawkey
import itertools

from gi.repository import Gio

from yumex.backend import YumexPackage
from yumex.ui.package_settings import InfoType, PackageFilter
from yumex.utils import log

from yumex.utils.enums import PackageAction, PackageState, SearchField


class DnfCallback:
    def __init__(self, win):
        self.win = win
        self.repo = MDProgress(self)

    def set_title(self, txt):
        self.win.progress.set_title(txt)

    def set_subtitle(self, txt):
        self.win.progress.set_subtitle(txt)


class UpdateInfo:
    """Wrapper class for dnf update advisories on a given po."""

    UPDINFO_MAIN = ["id", "title", "type", "description"]

    def __init__(self, po):
        self.po = po

    @staticmethod
    def advisories_iter(po):
        # FIXME: hawkey.package.get_advisories() is not public API
        return itertools.chain(
            po.get_advisories(hawkey.LT), po.get_advisories(hawkey.GT | hawkey.EQ)
        )

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


class MDProgress(dnf.callback.DownloadProgress):
    """Metadata Download callback handler."""

    def __init__(self, main):
        super(MDProgress, self).__init__()
        self.main: DnfCallback = main
        self._last_name = None

    def start(self, total_files, total_size):
        pass

    def end(self, payload, status, msg):
        name = str(payload)
        if status == dnf.callback.STATUS_OK:
            log(f" --> progress: {name} completed")

    def progress(self, payload, done):
        name = str(payload)
        if name != self._last_name:
            log(f" --> progress: {name} started")
            self.main.set_subtitle(_(f"Downloading repository information for {name}"))
            self._last_name = name


class Packages:
    """
    Get access to packages in the dnf (hawkey) sack in an easy way
    """

    def __init__(self, base: dnf.Base):
        self._base = base
        self.sack = base.sack
        self.query = self.sack.query()
        self._inst_na = self.query.installed()._na_dict()
        self._update_na = self.query.upgrades()._na_dict()

    def _filter_packages(self, pkg_list: list[dnf.package.Package]):
        """
        Filter a list of package objects and replace
        the installed ones with the installed object, instead
        of the available object
        """
        pkgs = []
        for pkg in pkg_list:
            ypkg = YumexPackage.from_dnf4(pkg)
            key = (pkg.name, pkg.arch)
            inst_pkg = self._inst_na.get(key, [None])[0]
            if inst_pkg:
                ypkg.set_installed()
            pkgs.append(ypkg)
        return pkgs

    @property
    def installed(self):
        """
        get installed packages
        """
        avail_na = self.query.available()._na_dict()
        pkgs = []
        for pkg in self.query.installed().run():
            key = (pkg.name, pkg.arch)
            repo_pkg = avail_na.get(key, [None])[0]
            if repo_pkg:
                ypkg = YumexPackage.from_dnf4(repo_pkg)
                ypkg.set_installed()
            else:
                ypkg = YumexPackage.from_dnf4(pkg, state=PackageState.INSTALLED)
            pkgs.append(ypkg)
        return pkgs

    @property
    def updates(self):
        """
        get available updates
        """
        return [
            YumexPackage.from_dnf4(pkg, state=PackageState.UPDATE)
            for pkg in self.query.upgrades().run()
        ]

    def filter_installed(self, query: dnf.query.Query):
        pkgs = []
        for pkg in query.run():
            ypkg = YumexPackage.from_dnf4(pkg)
            key = (pkg.name, pkg.arch)
            inst_pkg = self._inst_na.get(key, [None])[0]
            if inst_pkg:
                ypkg.set_installed()
            pkgs.append(ypkg)
        return pkgs

    @property
    def available(self) -> list[YumexPackage]:
        """
        newest available packages
        mark the installed ones
        """
        return self.filter_installed(query=self.query.available().latest())

    @property
    def extras(self):
        """
        installed packages, not in current repos
        """
        # anything installed but not in a repo is an extra
        avail_dict = self.query.available().pkgtup_dict()
        inst_dict = self.query.installed().pkgtup_dict()
        pkgs = []
        for pkgtup in inst_dict:
            if pkgtup not in avail_dict:
                pkgs.extend(inst_dict[pkgtup])
        return pkgs

    @property
    def obsoletes(self):
        """
        packages there is obsoleting some installed packages
        """
        inst = self.query.installed()
        return self.query.filter(obsoletes=inst)

    @property
    def recent(self, showdups=False):
        """
        Get the recent packages
        """
        recent = []
        now = time()
        recentlimit = now - (self._base.conf.recent * 86400)
        if showdups:
            avail = self.query.available()
        else:
            avail = self.query.latest()
        for po in avail:
            if int(po.buildtime) > recentlimit:
                recent.append(po)
        return recent

    def search(self, txt: str, field=SearchField.NAME):
        q = self.query.available()
        # field like *txt* and arch != src
        match field:
            case SearchField.NAME:
                fdict = {f"{field}__substr": txt, "arch__neq": "src"}
            case SearchField.SUMMARY:
                fdict = {f"{field}__substr": txt, "arch__neq": "src"}
            case SearchField.REPONAME, SearchField.ARCH:
                fdict = {f"{field}": txt}

        try:
            q = q.filter(hawkey.ICASE, **fdict).latest()
            return self.filter_installed(query=q)
        except AssertionError:
            return []

    def find_package(self, pkg: YumexPackage) -> dnf.package.Package:
        """Get the package from given package id."""
        q = self.query
        if pkg.state == PackageState.INSTALLED:  # installed package
            f = q.installed()
            f = f.filter(
                name=pkg.name, version=pkg.version, release=pkg.release, arch=pkg.arch
            ).run()
            if len(f) > 0:
                return f[0]
            else:
                return None
        else:
            f = q.available()
            f = f.filter(
                name=pkg.name, version=pkg.version, release=pkg.release, arch=pkg.arch
            ).run()
            if len(f) > 0:
                return f[0]
            else:
                return None


class DnfBase(dnf.Base):
    """
    class to encapsulate and extend the dnf.Base API
    """

    def __init__(self, callback, setup_sack=False):
        dnf.Base.__init__(self)
        # setup the dnf cache
        RELEASEVER = dnf.rpm.detect_releasever(self.conf.installroot)
        self.conf.substitutions["releasever"] = RELEASEVER
        # read the repository infomation
        self._packages = None
        self.read_all_repos()
        self.md_progress = callback.repo
        self.repos.all().set_progress_bar(self.md_progress)
        if setup_sack:
            # populate the dnf sack
            self.fill_sack()
            self._packages = Packages(self)  # Define a Packages object

    def setup_base(self):
        self.fill_sack()
        self._packages = Packages(self)  # Define a Packages object

    def package_remove(self, pkg):
        """FIXME: dnf.Base.package_remove is not public API and don't handle deps
        So we overload it and use the clean_deps=True, to handle deps removal

        We don't need all checks, that dnf does internally because we already know
        that the package is install
        """

        self._goal.erase(pkg, clean_deps=True)
        return 1

    @property
    def packages(self) -> Packages:
        """property to get easy acceess to packages"""
        if not self._packages:
            self.setup_base()
        return self._packages

    def cachedir_fit(self):
        conf = self.conf
        subst = conf.substitutions
        # this is not public API, same procedure as dnf cli
        suffix = dnf.conf.parser.substitute(dnf.const.CACHEDIR_SUFFIX, subst)
        cli_cache = dnf.conf.CliCache(conf.cachedir, suffix)
        return cli_cache.cachedir, cli_cache.system_cachedir

    def setup_cache(self):
        """Setup the dnf cache, same as dnf cli"""
        conf = self.conf
        conf.substitutions["releasever"] = dnf.rpm.detect_releasever("/")
        conf.cachedir, self._system_cachedir = self.cachedir_fit()

    def get_transaction(self):
        """Get current transaction"""
        tx_list = []
        replaces = {}
        if self.transaction:
            # build a reverse mapping to 'replaced_by'
            # this is required to achieve reasonable speed
            for tsi in self.transaction:
                if tsi.action != dnf.transaction.PKG_OBSOLETED:
                    continue
                for i in tsi._item.getReplacedBy():
                    replaces.setdefault(i, set()).add(tsi)

            for tsi in self.transaction:
                match tsi.action:
                    case dnf.transaction.PKG_DOWNGRADE:
                        tx_list.append(
                            YumexPackage.from_dnf4(
                                tsi.pkg,
                                state=PackageState.INSTALLED,
                                action=PackageAction.DOWNGRADE,
                            )
                        )
                    case dnf.transaction.PKG_ERASE:
                        tx_list.append(
                            YumexPackage.from_dnf4(
                                tsi.pkg,
                                state=PackageState.INSTALLED,
                                action=PackageAction.ERASE,
                            )
                        )
                    case dnf.transaction.PKG_INSTALL:
                        tx_list.append(
                            YumexPackage.from_dnf4(
                                tsi.pkg,
                                state=PackageState.AVAILABLE,
                                action=PackageAction.INSTALL,
                            )
                        )
                    case dnf.transaction.PKG_REINSTALL:
                        tx_list.append(
                            YumexPackage.from_dnf4(
                                tsi.pkg,
                                state=PackageState.INSTALLED,
                                action=PackageAction.REINSTALL,
                            )
                        )
                    case dnf.transaction.PKG_UPGRADE:
                        tx_list.append(
                            YumexPackage.from_dnf4(
                                tsi.pkg,
                                state=PackageState.UPDATE,
                                action=PackageAction.UPGRADE,
                            )
                        )
                    case _:
                        log(" BACKEND: unhandled transaction found: {tsi.action}")
        if replaces:
            log(f" BACKEND: replaces found {replaces}")
        return tx_list


class Backend(DnfBase):
    """
    Package backend base on dnf 4.x python API
    """

    def __init__(self, callback):
        DnfBase.__init__(self, callback)

    def reset_backend(self):
        self.reset(goal=True, repos=True, sack=True)
        self.setup_base()

    def get_packages(self, pkg_filter: PackageFilter) -> list[YumexPackage]:
        match pkg_filter:
            case PackageFilter.AVAILABLE:
                return self.packages.available
            case PackageFilter.INSTALLED:
                return self.packages.installed
            case PackageFilter.UPDATES:
                return self.packages.updates
            case _:
                return []

    def search(self, txt: str, field: str = "name") -> list[YumexPackage]:
        return self.packages.search(txt, field=field)

    def get_package_info(self, pkg: YumexPackage, attr: InfoType) -> Union[str, None]:
        dnf_pkg = self.packages.find_package(pkg)
        log(f" BACKEND: pkg: {dnf_pkg} attribute : {attr}")
        if dnf_pkg:
            match attr:
                case InfoType.DESCRIPTION:
                    return pkg.description
                case InfoType.FILES:
                    return dnf_pkg.files
                case InfoType.UPDATE_INFO:
                    updinfo = UpdateInfo(dnf_pkg)
                    value = updinfo.advisories_list()
                    return value
        return None

    def get_repositories(self):
        repos = self.repos.all()
        for repo in repos:
            if not repo.id.endswith("-source") and not repo.id.endswith("-debuginfo"):
                yield (repo.id, repo.name, repo.enabled)

    def depsolve(self, store: Gio.ListStore) -> list[YumexPackage]:
        """build a trasaction and retrun the dependencies"""
        self.reset(goal=True, sack=False, repos=False)  # clean current transaction
        nevra_dict = {}
        deps = []
        for pkg in store:
            dnf_pkg = self.packages.find_package(pkg)
            if dnf_pkg:
                nevra_dict[pkg.nevra] = pkg
                match pkg.state:
                    case PackageState.INSTALLED:
                        self.package_remove(dnf_pkg)
                        log(f" BACKEND: add {str(dnf_pkg)} to transaction for removal")
                    case PackageState.UPDATE:
                        self.package_upgrade(dnf_pkg)
                        log(f" BACKEND: add {str(dnf_pkg)} to transaction for upgrade")
                    case PackageState.AVAILABLE:
                        self.package_install(dnf_pkg)
                        log(
                            f" BACKEND: add {str(dnf_pkg)} to transaction for installation"
                        )
            else:
                log(f" BACKEND: dnf package for {pkg} was not found")
        try:
            res = self.resolve(allow_erasing=True)
            log(f" BACKEND: depsolve completted : {res}")
            for pkg in self.get_transaction():
                if pkg.nevra not in nevra_dict:
                    log(f" BACKEND: adding as dep : {pkg} ")
                    pkg.is_dep = True
                    deps.append(pkg)
                else:
                    log(f" BACKEND: skipping already in transaction : {pkg} ")

        except dnf.exceptions.DepsolveError as e:
            log(f" BACKEND: depsolve failed : {str(e)}")
        return deps
