"""
These tests use real dnf data from the current machine so they might take some time
to run. so they are disabled by default.
Some if the test might fail becuase their requiements is not found in the repository
Se comments on the individual tests

use:

pytest -m "dnftest"

to excute them.

"""
import pytest
from tests.mock import Mock
from yumex.backend.dnf import YumexPackage
from yumex.backend.dnf.dnf4 import Backend as Dnf4Backend
from yumex.utils.enums import PackageFilter, PackageState, SearchField

pytestmark = pytest.mark.dnftest


class MockCallback(Mock):
    def __init__(self):
        self.repo = None

    def set_title(self, txt):
        # self.win.progress.set_title(txt)
        pass

    def set_subtitle(self, txt):
        # self.win.progress.set_subtitle(txt)
        pass


@pytest.fixture
def backend():
    return Dnf4Backend(MockCallback())


def test_setup(backend):
    """Test we can create and dnf backend instance"""
    assert isinstance(backend, Dnf4Backend)


def test_get_repositorie(backend):
    """test the get_repositories method"""
    repos = list(backend.get_repositories())
    assert len(repos) > 0
    repo_id, repo_name, repo_enabled = repos[0]
    assert isinstance(repo_id, str) and repo_id != ""
    assert isinstance(repo_name, str) and repo_id != ""
    assert isinstance(repo_enabled, bool)


def test_get_packages_installed(backend):
    """test get_packages for installed packages"""
    pkgs = backend.get_packages(PackageFilter.INSTALLED)
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    assert isinstance(pkg, YumexPackage)
    assert pkg.state == PackageState.INSTALLED


def test_get_packages_available(backend):
    """test get_packages for availabe packages"""
    pkgs = backend.get_packages(PackageFilter.AVAILABLE)
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    assert isinstance(pkg, YumexPackage)
    assert pkg.state == PackageState.AVAILABLE


def test_get_packages_updates(backend):
    """test get_packages for upgradable"""
    pkgs = backend.get_packages(PackageFilter.UPDATES)
    assert isinstance(pkgs, list)
    if len(pkgs) > 0:
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
    assert isinstance(pkg, YumexPackage)
    assert pkg.name == "0xFFFF"


# will fail if the fedora repo is not available in repos
def test_search_repo(backend):
    """test search by repo"""
    pkgs = backend.search("fedora", field=SearchField.REPO)
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    assert isinstance(pkg, YumexPackage)
    assert pkg.repo == "fedora"


# will fail if Yum Extender is not installed or available in the repos
def test_search_desc(backend):
    """test search by summary"""
    pkgs = backend.search("Yum Extender", field=SearchField.SUMMARY)
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    assert isinstance(pkg, YumexPackage)
    assert "Yum Extender" in pkg.description


def test_search_arch(backend):
    """test search by arch"""
    pkgs = backend.search("noarch", field=SearchField.ARCH)
    assert isinstance(pkgs, list)
    assert len(pkgs) > 0
    pkg = pkgs[0]
    assert isinstance(pkg, YumexPackage)
    assert pkg.arch == "noarch"


def test_search_notfound(backend):
    """test search by name not found"""
    pkgs = backend.search("XXXNOTFOUNDXXX", field=SearchField.NAME)
    assert isinstance(pkgs, list)
    assert len(pkgs) == 0


def test_search_illegal_field(backend):
    """test search by illegal search field"""
    with pytest.raises(ValueError):
        _ = backend.search("ffff", field="illegal")


# TODO: Add tests for def reset_backend(self) -> None:
# TODO: Add tests for def get_package_info(self, pkg: YumexPackage, attr: InfoType) -> str | None:
# TODO: Add tests for def depsolve(self, pkgs: Iterable[YumexPackage]) -> list[YumexPackage]:
