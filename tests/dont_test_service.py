import pytest

from yumex.backend.dnf import YumexPackage
from yumex.service.dnf5daemon import Dnf5UpdateChecker


@pytest.fixture
def checker():
    with Dnf5UpdateChecker() as chk:
        yield chk


def test_session(checker):
    """Test the get_session function"""
    assert isinstance(checker, Dnf5UpdateChecker)
    assert checker.session is not None
    assert checker.iface_rpm is not None
    assert checker.iface_repo is not None


def test_get_repo_priorities(checker):
    """Test the get_repo_priorities function"""
    repo_priorities = checker.get_repo_priorities()
    assert isinstance(repo_priorities, dict)
    assert len(repo_priorities) > 0
    for repo, priority in repo_priorities.items():
        assert isinstance(repo, str)
        assert isinstance(priority, int)


def test_get_packages_by_name(checker, pkg_yumex):
    """Test the get_packages_by_name function"""
    assert isinstance(pkg_yumex, YumexPackage)
    packages = checker.get_packages_by_name(pkg_yumex)
    assert isinstance(packages, list)
    assert len(packages) > 0
    print()
    if packages:
        for package in packages:
            print(package, package.repo)
            assert isinstance(package, YumexPackage)
            assert package.name == pkg_yumex.name


def test_check_dnf_updates(checker):
    """Test the check_dnf_updates function"""
    updates = checker.check_updates(refresh=True)
    assert isinstance(updates, list)
    if updates:
        for update in updates:
            assert isinstance(update, YumexPackage)
