from turtle import update
import pytest  # noqa: F401


from unittest.mock import MagicMock, Mock, patch


def package_factory(name, version, epoch, repoid):
    pkg = Mock(name="Package")
    pkg.get_name.return_value = name
    pkg.get_version.return_value = version
    pkg.get_epoch.return_value = epoch
    pkg.get_repo_id.return_value = repoid
    pkg.get_evr.return_value = f"{name}-{epoch}:{version}"
    return pkg


def repo_factory(id: str, priority: int):
    repo = Mock(name="Repo")
    repo.get_id.return_value = id
    repo.get_priority.return_value = priority
    return repo


def packages_factory(names: list = ["pkg", "foo", "bar"]):
    pkg1 = package_factory("pkg", "2.0", "0", "test-repo1")
    pkg2 = package_factory("pkg", "2.0", "0", "test-repo2")
    pkg3 = package_factory("foo", "2.0", "0", "test-repo3")
    pkg4 = package_factory("bar", "2.0", "0", "test-repo4")
    pkgs = [pkg1, pkg2, pkg3, pkg4]
    mock = MagicMock()
    mock.__iter__.return_value = [pkg for pkg in pkgs if pkg.get_name() in names]
    return mock


def package_query_factory(names: list = ["pkg", "foo", "bar"]):
    query = MagicMock(name="PQ")
    query.__iter__.return_value = packages_factory(names)
    query.filter_name.return_value = None
    return query


def repo_query_factory():
    repo1 = repo_factory("test-repo1", 33)
    repo2 = repo_factory("test-repo2", 66)
    repo_query = MagicMock(name="RepoQuery")
    repo_query.__iter__.return_value = [repo1, repo2]
    return repo_query


@pytest.fixture
def base():
    base = Mock()
    return base


@patch("yumex.service.dnf5.PackageQuery")
def test_get_package_repos(mock_package_query: Mock, base):
    mock_package_query.return_value = package_query_factory(names=["pkg"])
    from yumex.service.dnf5 import get_package_repos

    res = get_package_repos(base, "pkg")
    assert isinstance(res, list)
    assert len(res) == 2
    assert "test-repo1" in res
    assert "test-repo2" in res


@patch("yumex.service.dnf5.RepoQuery")
def test_get_repo_priority(mock_repo_query, base: MagicMock):
    mock_repo_query.return_value = repo_query_factory()
    from yumex.service.dnf5 import get_repo_priority

    res = get_repo_priority(base, "test-repo1")
    assert res == 33
    res = get_repo_priority(base, "test-repo2")
    assert res == 66


@patch("yumex.service.dnf5.RepoQuery")
def test_get_repo_priority_default(mock_repo_query, base: MagicMock):
    mock_repo_query.return_value = repo_query_factory()
    from yumex.service.dnf5 import get_repo_priority

    res = get_repo_priority(base, "notfound")
    assert res == 99


@patch("yumex.service.dnf5.RepoQuery")
@patch("yumex.service.dnf5.PackageQuery")
def test_get_prioritied_packages(repo_query, package_query, base: Mock):
    repo_query.return_value = repo_query_factory()
    package_query.return_value = package_query_factory()
    from yumex.service.dnf5 import get_prioritied_packages

    updates = packages_factory(["pkg"])
    assert len(list(updates)) == 2
    res = get_prioritied_packages(updates, base)
    assert isinstance(res, list)
    assert len(res) == 1
    # print()
    for pkg in res:
        # print(pkg.get_evr(), pkg.get_repo_id())
        if pkg.get_name() == "pkg":  # wee should only get the the one with highest priority (test-repo1)
            assert pkg.get_repo_id() == "test-repo1"
