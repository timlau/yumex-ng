import pytest  # noqa: F401


from unittest.mock import MagicMock, Mock


def package_factory(name, version, epoch, repoid):
    pkg = Mock(name="Package")
    pkg.name = name
    pkg.version = version
    pkg.epoch = epoch
    pkg.reponame = repoid
    pkg.evr = f"{name}-{epoch}:{version}"
    return pkg


def repo_factory(id: str, priority: int):
    repo = Mock(name="Repo")
    repo.id = id
    repo.priority = priority
    return repo


def packages_factory(names: list = ["pkg", "foo", "bar"]):
    pkg1 = package_factory("pkg", "2.0", "0", "test-repo1")
    pkg2 = package_factory("pkg", "2.0", "0", "test-repo2")
    pkg3 = package_factory("foo", "2.0", "0", "test-repo3")
    pkg4 = package_factory("bar", "2.0", "0", "test-repo4")
    pkgs = [pkg1, pkg2, pkg3, pkg4]
    mock = MagicMock(name="packages")
    mock.__iter__.return_value = [pkg for pkg in pkgs if pkg.name in names]
    mock.run().__iter__.return_value = [pkg for pkg in pkgs if pkg.name in names]
    return mock


class MockRepos:
    def __init__(self) -> None:
        repo1 = repo_factory("test-repo1", 33)
        repo2 = repo_factory("test-repo2", 66)
        self._repos = {}
        self._repos[repo1.id] = repo1
        self._repos[repo2.id] = repo2

    def get(self, id: str):
        return self._repos.get(id, None)


@pytest.fixture
def base():
    def pkg_filter(name):
        return packages_factory([name])

    base = Mock(name="base")
    base.repos = MockRepos()
    base.sack.query().available().filter = pkg_filter
    return base


def test_sack(base):
    res = base.sack.query().available().filter("pkg").run()
    # print()
    pkgs = list(res)
    assert len(pkgs) == 2
    for pkg in pkgs:
        # print(pkg.evr, pkg.reponame)
        assert pkg.reponame in ["test-repo1", "test-repo2"]
        assert pkg.name == "pkg"


def test_get_package_repos(base):
    from yumex.service.dnf4 import get_package_repos

    res = get_package_repos(base, "pkg")
    assert isinstance(res, list)
    assert len(res) == 2
    assert "test-repo1" in res
    assert "test-repo2" in res


def test_get_repo_priority(base: MagicMock):
    from yumex.service.dnf4 import get_repo_priority

    res = get_repo_priority(base, "test-repo1")
    assert res == 33
    res = get_repo_priority(base, "test-repo2")
    assert res == 66


def test_get_repo_priority_default(base: MagicMock):
    from yumex.service.dnf4 import get_repo_priority

    res = get_repo_priority(base, "notfound")
    assert res == 99


def test_get_prioritied_packages(base: Mock):
    from yumex.service.dnf4 import get_prioritied_packages

    updates = packages_factory(["pkg"])
    assert len(list(updates)) == 2
    res = get_prioritied_packages(base, updates)
    assert isinstance(res, list)
    assert len(res) == 1
    print()
    for pkg in res:
        print(pkg.evr, pkg.reponame)
        if pkg.name == "pkg":  # wee should only get the the one with highest priority (test-repo1)
            assert pkg.reponame == "test-repo1"
