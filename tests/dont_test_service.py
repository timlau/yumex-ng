import pytest

from yumex.backend.dnf import YumexPackage
from yumex.service.dnf5daemon import (
    check_dnf_updates,
    close_session,
    get_packages_by_name,
    get_repo_priorities,
    open_session,
)


@pytest.fixture
def session():
    session = open_session()
    yield session
    close_session(session)


def test_get_session(session):
    """Test the get_session function"""
    assert isinstance(session, str)


def test_get_repo_priorities(session):
    """Test the get_repo_priorities function"""
    repo_priorities = get_repo_priorities(session)
    assert isinstance(repo_priorities, dict)
    assert len(repo_priorities) > 0
    for repo, priority in repo_priorities.items():
        assert isinstance(repo, str)
        assert isinstance(priority, int)


def test_get_packages_by_name(session):
    """Test the get_packages_by_name function"""
    package_name = "yumex"
    packages = get_packages_by_name(session, package_name)
    assert isinstance(packages, list)
    assert len(packages) > 0
    print()
    if packages:
        for package in packages:
            print(package, package.repo)
            assert isinstance(package, YumexPackage)
            assert package.name == package_name


def test_check_dnf_updates():
    """Test the check_dnf_updates function"""
    updates = check_dnf_updates(refresh=True)
    assert isinstance(updates, list)
    if updates:
        for update in updates:
            assert isinstance(update, YumexPackage)
