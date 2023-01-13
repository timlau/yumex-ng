import pytest

from yumex.backend.dnf import YumexPackage


@pytest.fixture
def pkg_dict():
    return {
        "name": "mypkg",
        "version": "1",
        "arch": "x86_64",
        "release": "1.0",
        "epoch": "",
        "repo": "repo",
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
        "repo": "repo",
        "description": "desc",
        "size": 1024,
    }


@pytest.fixture
def pkg(pkg_dict):
    return YumexPackage(**pkg_dict)


@pytest.fixture
def pkg_upd(pkg_dict_upd):
    return YumexPackage(**pkg_dict_upd)
