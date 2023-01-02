from collections import namedtuple
from typing import Union

from gi.repository import Gio

from libdnf5.base import Base
from libdnf5.rpm import PackageQuery, Package  # noqa: F401
from libdnf5.repo import RepoQuery  # noqa : F401
from libdnf5.common import QueryCmp_NEQ

from yumex.backend import SearchField, YumexPackage, PackageState
from yumex.ui.package_settings import InfoType, PackageFilter  # noqa :F401

PackageTuple = namedtuple(
    "package",
    [
        "name",
        "arch",
        "version",
        "release",
        "epoch",
        "reponame",
        "summary",
        "size",
    ],
)


def get_yumex_package(pkg: Package):
    name = pkg.get_name()
    arch = pkg.get_arch()
    version = pkg.get_version()
    release = pkg.get_release()
    epoch = pkg.get_epoch()
    if pkg.is_installed():
        reponame = pkg.get_from_repo_id()
    else:
        reponame = pkg.get_repo_id()
    summary = pkg.get_summary()
    size = pkg.get_package_size()
    po = PackageTuple(name, arch, version, release, epoch, reponame, summary, size)
    return YumexPackage(po)


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


class Backend(Base):
    def __init__(self, *args) -> None:
        super().__init__(*args)
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
        query.filter_earliest_evr()
        return query

    @property
    def updates(self) -> PackageQuery:
        query = PackageQuery(self)
        query.filter_upgrades()
        return query

    def _get_yumex_packages(self, query: PackageQuery):
        for pkg in query:
            ypkg: YumexPackage = get_yumex_package(pkg)
            if pkg.is_installed():
                ypkg.set_installed()
            yield ypkg

    def search(self, key: str, field: SearchField) -> list[YumexPackage]:
        query = PackageQuery(self)
        match field:
            case SearchField.NAME:
                query.filter_name(key)
                query.filter_arch("src", QueryCmp_NEQ)
            case SearchField.ARCH:
                query.filter_arch(key)
            case SearchField.REPONAME:
                query.filter_repo_id(key)
        return self._get_yumex_packages(query)

    def get_packages(self, pkg_filter: PackageFilter) -> list[YumexPackage]:
        match pkg_filter:
            case PackageFilter.AVAILABLE:
                return list(self._get_yumex_packages(self.available))
            case PackageFilter.INSTALLED:
                return list(self._get_yumex_packages(self.installed))
            case PackageFilter.UPDATES:
                return list(self._get_yumex_packages(self.updates))

    def get_package_info(self, pkg: YumexPackage, attr: InfoType) -> Union[str, None]:
        query = PackageQuery(self)
        if pkg.state == PackageState.AVAILABLE:
            query.filter_available()
        else:
            query.filter_available()
        query.filter_nevra([pkg.nevra])
        pkgs = list(query)
        print(pkg.nevra, pkgs)
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
        return None

    def get_repositories(self) -> list[str]:  # TODO: Implement
        return ["fedora"]

    def depsolve(self, store: Gio.ListStore) -> list[YumexPackage]:
        return None  # TODO: implement

    def test(self):
        nevra = "aajohan-comfortaa-fonts-0:3.101-5.fc37.noarch"
        query = PackageQuery(self)
        query.filter_nevra(nevra)
        for pkg in query:
            if pkg.is_installed():
                print(pkg.get_nevra(), pkg.get_from_repo_id())
            else:
                print(pkg.get_nevra(), pkg.get_repo_id())


if __name__ == "__main__":
    backend = Backend()
    backend.test()