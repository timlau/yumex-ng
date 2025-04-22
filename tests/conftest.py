import pytest

from yumex.backend.dnf import YumexPackage


def pytest_addoption(parser):
    parser.addoption(
        "--guitest",
        action="store_true",
        dest="guitest",
        default=False,
        help="enable gui tests",
    )


@pytest.fixture
def pkg_dict():
    return {
        "name": "mypkg",
        "version": "1",
        "arch": "x86_64",
        "release": "1.0",
        "epoch": "",
        "repo": "repo2",
        "description": "desc",
        "size": 2048,
    }


@pytest.fixture
def pkg_other_dict():
    return {
        "name": "otherpkg",
        "version": "1",
        "arch": "noarch",
        "release": "1.0",
        "epoch": "",
        "repo": "repo1",
        "description": "desc",
        "size": 1024,
    }


@pytest.fixture
def pkg_dict_upd():
    return {
        "name": "mypkg",
        "version": "2",
        "arch": "x86_64",
        "release": "2.0",
        "epoch": "",
        "repo": "repo1",
        "description": "desc",
        "size": 1024,
    }


@pytest.fixture
def pkg_dict_yumex():
    return {
        "name": "yumex",
        "version": "5.3.1",
        "arch": "noarch",
        "release": "1.fc42",
        "epoch": "",
        "repo": "repo1",
        "description": "desc",
        "size": 1024,
    }


@pytest.fixture
def pkg_yumex(pkg_dict_yumex) -> YumexPackage:
    return YumexPackage(**pkg_dict_yumex)


@pytest.fixture
def pkg(pkg_dict) -> YumexPackage:
    return YumexPackage(**pkg_dict)


@pytest.fixture
def pkg_other(pkg_other_dict) -> YumexPackage:
    return YumexPackage(**pkg_other_dict)


@pytest.fixture
def pkg_upd(pkg_dict_upd) -> YumexPackage:
    return YumexPackage(**pkg_dict_upd)
