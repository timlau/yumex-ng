import pytest

from gi.repository import Gio
from yumex.utils.enums import SortType
from yumex.utils.storage import PackageStorage


@pytest.fixture
def storage() -> PackageStorage:
    return PackageStorage()


def test_storage_setup(storage):
    assert isinstance(storage.get_storage(), Gio.ListStore)


def test_storage_add_pkg(storage, pkg):
    storage.add_package(pkg)
    assert len(storage) == 1
    assert storage.get_storage()[0] == pkg


def test_storage_add_pkgs(storage, pkg, pkg_other):
    storage.add_packages([pkg, pkg_other])
    assert len(storage) == 2
    assert storage.get_storage()[0] == pkg
    assert storage.get_storage()[1] == pkg_other


def test_storage_contains(storage, pkg, pkg_other):
    storage.add_packages([pkg])
    assert pkg in storage
    assert pkg_other not in storage


def test_storage_iterate(storage, pkg, pkg_other):
    storage.add_packages([pkg, pkg_other])
    assert len(storage) == 2
    for ndx, po in enumerate(storage):
        match ndx:
            case 0:
                assert po == pkg
            case 1:
                assert po == pkg_other
            case _:
                raise IndexError("There should not be more than 2 packages in store")


def test_storage_clear(storage, pkg, pkg_other):
    """test clear()"""

    storage.add_packages([pkg, pkg_other])
    assert len(storage.get_storage()), 2
    current_id = id(storage.get_storage())
    store = storage.clear()
    assert id(store) != current_id
    assert len(storage) == 0


def test_storage_insert_sorted(storage, pkg, pkg_other):
    """test sort by name"""
    storage.add_package(pkg_other)
    storage.insert_sorted(pkg, lambda a, b: a.name > b.name)
    assert storage.get_storage()[0] == pkg
    assert storage.get_storage()[1] == pkg_other


def test_storage_sort_name(storage, pkg, pkg_other):
    """test sort by name"""
    storage.add_packages([pkg_other, pkg])  # otherpkg, mypkg
    storage.sort_by(SortType.NAME)  # mypkg, otherpkg
    assert storage.get_storage()[0] == pkg
    assert storage.get_storage()[1] == pkg_other


def test_storage_sort_repo(storage, pkg, pkg_other):
    """test sort by repo"""
    storage.add_packages([pkg, pkg_other])  # repo2, repo1
    storage.sort_by(SortType.REPO)  # repo1, repo2
    assert storage.get_storage()[0] == pkg_other
    assert storage.get_storage()[1] == pkg


def test_storage_sort_size(storage, pkg, pkg_other):
    """test sort by size"""
    storage.add_packages([pkg, pkg_other])  # 2048, 1024
    storage.sort_by(SortType.SIZE)  # 1024, 2048
    assert storage.get_storage()[0] == pkg_other
    assert storage.get_storage()[1] == pkg


def test_storage_sort_arch(storage, pkg, pkg_other):
    """test sort by size"""
    storage.add_packages([pkg, pkg_other])  # x86_64, noarch
    storage.sort_by(SortType.ARCH)  # noarch, x86_64
    assert storage.get_storage()[0] == pkg_other
    assert storage.get_storage()[1] == pkg


def test_storage_sort_illegal(storage, pkg, pkg_other):
    """test sort by illegal type"""
    with pytest.raises(ValueError):
        storage.add_packages([pkg, pkg_other])  # x86_64, noarch
        storage.sort_by("notfound")  # noarch, x86_64


def test_storage_add_illegal(storage, pkg, pkg_other):
    """test adding illegal datatypes"""
    with pytest.raises(ValueError):
        storage.add_packages([pkg, pkg_other, "illegal"])
    with pytest.raises(ValueError):
        storage.add_packages([pkg, pkg_other, None])


def test_storage_find_by_nevra(storage, pkg, pkg_other, pkg_upd):
    storage.add_packages([pkg, pkg_other])  # x86_64, noarch
    po = storage.find_by_nevra(pkg.nevra)  # pkg is in storage
    assert po == pkg
    po = storage.find_by_nevra(pkg_upd.nevra)  # pkg is not in storage
    assert po is None
