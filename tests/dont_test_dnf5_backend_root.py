"""
These tests use real dnf5 data from the current machine so they might take some time
to run. so they are not run by default.
Some if the test might fail becuase their requiements is not found in the repository
Se comments on the individual tests

use:

pytest tests/dont_test_dnf5_backend.py

to excute the test

"""

from dataclasses import fields

import pytest

from yumex.backend.dnf import YumexPackage
from yumex.backend.dnf5daemon import UpdateInfo, YumexRootBackend, create_package
from yumex.utils import setup_logging
from yumex.utils.enums import InfoType, PackageFilter, PackageState
from yumex.utils.exceptions import YumexException

from .mock import mock_presenter

setup_logging(debug=True)


@pytest.fixture
def presenter():
    """use a mock window"""
    return mock_presenter()


@pytest.fixture
def backend(presenter):
    backend = YumexRootBackend(presenter=presenter)
    yield backend
    backend.close()
    del backend


@pytest.fixture()
def package():
    return {
        "arch": "x86_64",
        "evr": "2.4.2-3.fc42",
        "install_size": 257602,
        "is_installed": True,
        "name": "Box2D",
        "repo_id": "@System",
        "summary": "A 2D Physics Engine for Games",
    }


@pytest.fixture()
def package_epoch():
    return {
        "arch": "x86_64",
        "evr": "4:2.4.2-3.fc42",
        "install_size": 257602,
        "is_installed": False,
        "name": "Box2D",
        "repo_id": "@System",
        "summary": "A 2D Physics Engine for Games",
    }


@pytest.fixture()
def yumex_package() -> YumexPackage:
    return create_package(
        {
            "arch": "x86_64",
            "evr": "2.4.2-3.fc42",
            "install_size": 257602,
            "is_installed": False,
            "name": "NOTFOUND",
            "repo_id": "@System",
            "summary": "This package don't exist",
        }
    )


def test_setup(backend):
    """Test we can create and dnf backend instance"""
    assert isinstance(backend, YumexRootBackend)


def test_installed(backend: YumexRootBackend):
    installed = backend.installed
    assert isinstance(installed, list)
    assert len(installed) > 0
    pkg = installed[0]
    pkg.pop("id")
    print(f"\ninstalled packages : {len(installed)}")
    print(pkg)
    expected_attr = backend.package_attr
    assert sorted(expected_attr) == sorted(pkg.keys())


def test_updates(backend: YumexRootBackend):
    updates = backend.updates
    print(f"\nUpdates : {updates}")
    assert isinstance(updates, list)
    if updates:
        pkg = updates[0]
        pkg.pop("id")
        print(f"Number of updates : {len(updates)}")
        print(pkg)
        expected_attr = backend.package_attr
        assert sorted(expected_attr) == sorted(pkg.keys())


def test_available(backend: YumexRootBackend):
    available = backend.available
    assert isinstance(available, list)
    assert len(available) > 0
    pkg = available[0]
    pkg.pop("id")
    print(f"\ninstalled packages : {len(available)}")
    print(pkg)
    expected_attr = backend.package_attr
    assert sorted(expected_attr) == sorted(pkg.keys())


def test_create_package(package):
    ypkg = create_package(package)
    assert isinstance(ypkg, YumexPackage)
    assert ypkg.epoch == 0
    assert ypkg.name == "Box2D"
    assert ypkg.version == "2.4.2"
    assert ypkg.release == "3.fc42"
    assert ypkg.arch == "x86_64"
    assert ypkg.description == "A 2D Physics Engine for Games"
    assert ypkg.repo == "@System"
    assert ypkg.state == PackageState.INSTALLED
    assert ypkg.size == 257602


def test_create_package_epoch(package_epoch):
    ypkg = create_package(package_epoch)
    assert isinstance(ypkg, YumexPackage)
    assert ypkg.epoch == "4"
    assert ypkg.name == "Box2D"
    assert ypkg.version == "2.4.2"
    assert ypkg.release == "3.fc42"
    assert ypkg.arch == "x86_64"
    assert ypkg.description == "A 2D Physics Engine for Games"
    assert ypkg.repo == "@System"
    assert ypkg.state == PackageState.AVAILABLE
    assert ypkg.size == 257602


def test_get_repositories(backend):
    """test the get_repositories method"""
    repos = list(backend.get_repositories())
    assert len(repos) > 0
    repo_id, repo_name, repo_enabled, priority = repos[0]
    assert isinstance(repo_id, str) and repo_id != ""
    assert isinstance(repo_name, str) and repo_name != ""
    assert isinstance(priority, int)
    assert repo_enabled in (True, False)


def test_get_packages_installed(backend):
    """test get_packages for installed packages"""
    pkgs = backend.get_packages(PackageFilter.INSTALLED)
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    print(f"\n# of packages : {len(pkgs)}")
    pkg = pkgs[0]
    assert isinstance(pkg, YumexPackage)
    assert pkg.state == PackageState.INSTALLED


def test_get_packages_available(backend):
    """test get_packages for availabe packages"""
    pkgs = backend.get_packages(PackageFilter.AVAILABLE)
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    print(f"\n# of packages : {len(pkgs)}")
    pkg = pkgs[0]
    assert isinstance(pkg, YumexPackage)
    assert pkg.state == PackageState.AVAILABLE


def test_get_packages_updates(backend):
    """test get_packages for upgradable"""
    pkgs = backend.get_packages(PackageFilter.UPDATES)
    assert isinstance(pkgs, list)
    if len(pkgs) > 0:
        print(f"\n# of packages : {len(pkgs)}")
        pkg = pkgs[0]
        assert isinstance(pkg, YumexPackage)
        assert pkg.state == PackageState.UPDATE


def test_get_packages_illegal(backend):
    """test get_packages with illegal package filter"""
    with pytest.raises(ValueError):
        _ = backend.get_packages("notfound")


# will fail if 0xFFFF package is not available in repos
def test_search_name(backend):
    """test search by name"""
    pkgs = backend.search("FFFF")
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    print()
    print(len(pkgs))
    print(pkg)
    assert isinstance(pkg, YumexPackage)
    assert pkg.name == "0xFFFF"


# will fail if the fedora repo is not available in repos
def test_search_repo(backend):
    """test search by repo"""
    options = {
        "repo": ["fedora"],
    }
    pkgs = backend.search("*", options)
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    print()
    print(len(pkgs))
    print(pkg)
    assert isinstance(pkg, YumexPackage)
    assert pkg.repo == "fedora"


def test_search_arch(backend):
    """test search by arch"""
    options = {
        "arch": ["noarch"],
    }
    pkgs = backend.search("noarch", options)
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    print()
    print(f"Number of packages : {len(pkgs)}")
    pkg = pkgs[0]
    assert isinstance(pkg, YumexPackage)
    assert pkg.arch == "noarch"


def test_search_notfound(backend):
    """test search by name not found"""
    pkgs = backend.search("XXXNOTFOUNDXXX")
    assert isinstance(pkgs, list)
    assert len(pkgs) == 0


def test_package_info_desc(backend):
    pkgs = backend.search("FFFF")
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    desc = backend.get_package_info(pkg, InfoType.DESCRIPTION)
    print()
    print(desc)
    assert isinstance(desc, str)
    assert len(desc) > 0
    assert "The 'Open Free Fiasco Firmware Flasher'" in desc


def test_package_info_files(backend):
    pkgs = backend.search("FFFF")
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    files = backend.get_package_info(pkg, InfoType.FILES)
    print()
    print(files)
    assert isinstance(files, list)
    assert len(files) > 0
    assert "/usr/bin/0xFFFF" in files


def test_package_info_files_0ad(backend):
    pkgs = backend.search("0ad")
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    files = backend.get_package_info(pkg, InfoType.FILES)
    print()
    print(files)
    assert isinstance(files, list)
    assert len(files) > 0
    assert "/usr/bin/pyrogenesis" in files


def test_package_info_files_notfound(backend, yumex_package):
    files = backend.get_package_info(yumex_package, InfoType.FILES)
    assert isinstance(files, list)
    assert len(files) == 0


# Advisory info is not working yet
def test_package_info_update(backend):
    pkgs = backend.search("dnf5")
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    upd_infos = backend.get_package_info(pkg, InfoType.UPDATE_INFO)
    print()
    print(upd_infos)
    assert isinstance(upd_infos, list)
    if len(upd_infos) > 0:
        # the elemeent sould match the fields in the UpdateInfo structure
        names = fields(UpdateInfo)
        for name in names:
            assert name.name in upd_infos[0]


def test_package_depsolve(backend):
    pkgs = backend.search("0ad")
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    print()
    ypkgs = backend.depsolve([pkg])
    assert isinstance(ypkgs, list)
    assert len(ypkgs) > 0
    ypkg = ypkgs[-1]
    print(ypkg)
    assert isinstance(ypkg, YumexPackage)
    assert ypkg.is_dep


# Require root access, so will ask for polkit auth
@pytest.mark.skip
def test_clean(backend: YumexRootBackend):
    result = backend.client.clean("expire-cache")
    assert result[0]


def test_exception(backend: YumexRootBackend):
    """Test the @yumex.utils.dbus_exception decorator does the right thing"""
    with pytest.raises(YumexException):
        backend.client._test_exception()


def test_get_packages_by_name(backend, pkg_yumex):
    """test search by name"""
    pkgs = backend.get_packages_by_name(pkg_yumex)
    print()
    print(f"\n# of packages : {len(pkgs)}")
    print(pkgs)
    assert isinstance(pkgs, list)
    assert len(pkgs) > 1
    pkg = pkgs[0]
    assert isinstance(pkg, YumexPackage)
    assert pkg.name == "yumex"
