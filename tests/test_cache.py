import pytest

from typing import Generator

from tests.mock import mock_package_backend

from yumex.backend.cache import YumexPackageCache
from yumex.backend.dnf import YumexPackage
from yumex.utils.enums import PackageFilter, PackageState


def test_get_package(pkg, pkg_dict):
    """should return the same package object, when adding another with same properties"""
    cache = YumexPackageCache(None)
    pkg.state = PackageState.INSTALLED
    po1 = cache.get_package(pkg)
    pkg2 = YumexPackage(**pkg_dict)
    po2 = cache.get_package(pkg2)
    assert id(pkg2) != id(pkg)  # different objects
    assert id(po1) == id(po2)  # returm objects should be the samme


@pytest.mark.parametrize(
    "first_state, second_state, expected_state",
    [
        (PackageState.AVAILABLE, PackageState.UPDATE, PackageState.UPDATE),
        (PackageState.INSTALLED, PackageState.UPDATE, PackageState.UPDATE),
        (PackageState.AVAILABLE, PackageState.INSTALLED, PackageState.INSTALLED),
        (PackageState.INSTALLED, PackageState.AVAILABLE, PackageState.INSTALLED),
    ],
)
def test_get_package_state_updates(
    first_state, second_state, expected_state, pkg, pkg_dict
):
    """Should update state, in some given combinations"""
    cache = YumexPackageCache(None)
    pkg.state = first_state
    cache.get_package(pkg)
    pkg2 = YumexPackage(**pkg_dict)
    pkg2.set_state(second_state)
    po2 = cache.get_package(pkg2)
    assert id(po2) == id(pkg)  # same object
    assert po2.state == expected_state  # state should be updated from pkg2


def test_get_packages(pkg, pkg_other):
    """Should return an interator to the cached packages"""
    cache = YumexPackageCache(None)
    res = cache.get_packages([pkg, pkg_other])
    assert isinstance(res, Generator)
    pkgs = list(res)
    assert pkgs == [pkg, pkg_other]


def test_get_packages_by_filter():
    """should get packages by filter, from the backend"""
    backend = mock_package_backend()
    cache = YumexPackageCache(backend)
    res = cache.get_packages_by_filter(PackageFilter.INSTALLED)
    assert isinstance(res, list)
    backend.get_packages.assert_called_with(PackageFilter.INSTALLED)


def test_get_packages_by_filter_illegal_filter():
    """should raise an exception if filter is illegal"""
    backend = mock_package_backend()
    cache = YumexPackageCache(backend)
    with pytest.raises(KeyError):
        _ = cache.get_packages_by_filter("notfound")


def test_get_packages_by_filter_two_times():
    """should only call the backend the first time and return the cached ones, second time"""
    backend = mock_package_backend()
    cache = YumexPackageCache(backend)
    res = cache.get_packages_by_filter(PackageFilter.AVAILABLE)
    po1 = res[0]
    res = cache.get_packages_by_filter(PackageFilter.AVAILABLE)
    po2 = res[0]
    assert id(po1) == id(po2)
    assert backend.get_packages.call_count == 1


def test_get_packages_by_filter_reset():
    """Should call the backend again after a reset"""
    backend = mock_package_backend()
    cache = YumexPackageCache(backend)
    res = cache.get_packages_by_filter(PackageFilter.AVAILABLE)
    po1 = res[0]
    res = cache.get_packages_by_filter(PackageFilter.AVAILABLE, reset=True)
    po2 = res[0]
    assert id(po1) == id(po2)
    # on reset the packages is reloaded from backend
    assert backend.get_packages.call_count == 2
