import pytest

from gi.repository import Gio
from yumex.backend.dnf import YumexPackage
from yumex.utils.storage import PackageStorage


class MockPresenter:
    def __init__(self) -> None:
        pass

    @property
    def backend(self) -> None:
        return None

    @property
    def package_cache(self) -> None:
        return None

    @property
    def progress(self) -> None:
        return None

    def reset_backend(self) -> None:
        pass

    def reset_cache(self) -> None:
        pass


@pytest.fixture
def storage() -> PackageStorage:
    return PackageStorage(YumexPackage, MockPresenter())


def test_storage_setup(storage):
    assert isinstance(storage.get_storage(), Gio.ListStore)


def test_storage_add(storage, pkg, other_pkg):
    storage.add_packages([pkg, other_pkg])
    assert storage.get_storage()[0], pkg
