import pytest  # noqa: F401


from unittest.mock import MagicMock
import libdnf5  # noqa: F401


@pytest.fixture
def repo_query():
    repo = MagicMock()
    repo.get_id.return_value = "test-repo"
    repo.get_priority.return_value = 33
    repo_query = MagicMock()
    repo_query.return_value = [repo]
    return repo_query


@pytest.fixture
def package_query():
    package_query = MagicMock()
    package_query.filter_name.return_value = []
    return package_query


@pytest.fixture
def base(monkeypatch: pytest.MonkeyPatch, repo_query: MagicMock, package_query: MagicMock):
    monkeypatch.setattr("libdnf5.rpm.PackageQuery", package_query)
    monkeypatch.setattr("libdnf5.repo.RepoQuery", repo_query)
    base = MagicMock()
    return base


def test_get_package_repos(base: MagicMock):
    from yumex.service.dnf5 import get_package_repos

    res = get_package_repos(base, "some_package")

    assert isinstance(res, list)


def test_get_repo_priority_default(base: MagicMock):
    from yumex.service.dnf5 import get_repo_priority

    res = get_repo_priority(base, "test-repo")
    assert res == 33


def test_get_repo_priority(base: MagicMock):
    from yumex.service.dnf5 import get_repo_priority

    res = get_repo_priority(base, "test-repo")
    assert res == 33
