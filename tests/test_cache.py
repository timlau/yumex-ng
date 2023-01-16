import pytest

from typing import Generator

from yumex.backend.cache import YumexPackageCache
from yumex.backend.dnf import YumexPackage
from yumex.utils.enums import PackageFilter, PackageState


BASE_DICT = {
    "version": "1",
    "arch": "x86_64",
    "release": "1.0",
    "epoch": "",
    "repo": "repo",
    "description": "desc",
    "size": 1024,
}


class MockBackend:
    def __init__(self):
        self.filters = []
        self.packages = {
            PackageFilter.INSTALLED: [
                YumexPackage(name="inst1", **BASE_DICT),
                YumexPackage(name="inst2", **BASE_DICT),
            ],
            PackageFilter.AVAILABLE: [
                YumexPackage(name="avail1", **BASE_DICT),
                YumexPackage(name="avail2", **BASE_DICT),
            ],
            PackageFilter.UPDATES: [],
        }

    def get_packages(self, pkg_filter: PackageFilter) -> list[YumexPackage]:
        self.filters.append(pkg_filter)
        return self.packages[pkg_filter]


def test_get_package(pkg, pkg_dict):
    """test that a package is cached"""
    cache = YumexPackageCache(None)
    assert cache._package_dict == {}
    pkg.state = PackageState.INSTALLED
    po1 = cache.get_package(pkg)
    assert pkg in cache._package_dict
    pkg2 = YumexPackage(**pkg_dict)
    po2 = cache.get_package(pkg2)
    assert id(po1) == id(po2)


def test_get_package_update_after_available(pkg, pkg_dict):
    """test that package state is updated"""
    cache = YumexPackageCache(None)
    pkg.state = PackageState.AVAILABLE
    cache.get_package(pkg)
    pkg2 = YumexPackage(**pkg_dict)
    pkg2.set_state(PackageState.UPDATE)
    po2 = cache.get_package(pkg2)
    assert po2.state == PackageState.UPDATE


def test_get_package_update_after_installed(pkg, pkg_dict):
    """test that package state is updated"""
    cache = YumexPackageCache(None)
    pkg.state = PackageState.INSTALLED
    cache.get_package(pkg)
    pkg2 = YumexPackage(**pkg_dict)
    pkg2.set_state(PackageState.UPDATE)
    po2 = cache.get_package(pkg2)
    assert po2.state == PackageState.UPDATE


def test_get_package_installed_after_available(pkg, pkg_dict):
    """test that package state is updated"""
    cache = YumexPackageCache(None)
    pkg.state = PackageState.AVAILABLE
    cache.get_package(pkg)
    pkg2 = YumexPackage(**pkg_dict)
    pkg2.set_state(PackageState.INSTALLED)
    po2 = cache.get_package(pkg2)
    assert po2.state == PackageState.INSTALLED


def test_get_package_available_after_installed(pkg, pkg_dict):
    """test that package state is not updated"""
    cache = YumexPackageCache(None)
    pkg.state = PackageState.INSTALLED
    cache.get_package(pkg)
    pkg2 = YumexPackage(**pkg_dict)
    pkg2.state = PackageState.AVAILABLE
    po2 = cache.get_package(pkg2)
    assert po2.state == PackageState.INSTALLED


def test_get_packages(pkg, pkg_other):
    """test the get_packages method"""
    cache = YumexPackageCache(None)
    res = cache.get_packages([pkg, pkg_other])
    assert isinstance(res, Generator)
    pkgs = list(res)
    assert len(pkgs) == 2
    assert pkg in pkgs
    assert pkg_other in pkgs


def test_get_packages_by_filter_inst():
    """test the get_packages_by_filter method (installed)"""
    cache = YumexPackageCache(MockBackend())
    res = cache.get_packages_by_filter(PackageFilter.INSTALLED)
    assert isinstance(res, list)
    assert len(res) == 2
    assert res[0].name == "inst1"


def test_get_packages_by_filter_avail():
    """test the get_packages_by_filter method (available)"""
    cache = YumexPackageCache(MockBackend())
    res = cache.get_packages_by_filter(PackageFilter.AVAILABLE)
    assert isinstance(res, list)
    assert len(res) == 2
    assert res[0].name == "avail1"


def test_get_packages_by_filter_three_times():
    """test the get_packages_by_filter dont reload from backend"""
    backend = MockBackend()
    cache = YumexPackageCache(backend)
    res = cache.get_packages_by_filter(PackageFilter.AVAILABLE)
    po1 = res[0]
    res = cache.get_packages_by_filter(PackageFilter.AVAILABLE)
    po2 = res[0]
    res = cache.get_packages_by_filter(PackageFilter.AVAILABLE)
    po3 = res[0]
    assert id(po1) == id(po2) == id(po3)
    assert len(backend.filters) == 1
    assert backend.filters[0] == PackageFilter.AVAILABLE


def test_get_packages_by_filter_reset():
    """test the get_packages_by_filter reset"""
    backend = MockBackend()
    cache = YumexPackageCache(backend)
    res = cache.get_packages_by_filter(PackageFilter.AVAILABLE)
    po1 = res[0]
    res = cache.get_packages_by_filter(PackageFilter.AVAILABLE, reset=True)
    po2 = res[0]
    res = cache.get_packages_by_filter(PackageFilter.AVAILABLE)
    po3 = res[0]
    assert id(po1) == id(po2) == id(po3)
    # on reset the packages is reloaded from backend
    assert len(backend.filters) == 2
    assert backend.filters[0] == PackageFilter.AVAILABLE


def test_get_packages_by_filter_updates():
    """test the get_packages_by_filter method (updated)"""
    cache = YumexPackageCache(MockBackend())
    res = cache.get_packages_by_filter(PackageFilter.UPDATES)
    assert isinstance(res, list)
    assert len(res) == 0


def test_get_packages_by_filter_notfound():
    """test the get_packages_by_filter with illegal filter"""
    cache = YumexPackageCache(MockBackend())
    with pytest.raises(KeyError):
        _ = cache.get_packages_by_filter("notfound")
