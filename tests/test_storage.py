import pytest
from gi.repository import Gio

from yumex.utils.enums import SortType
from yumex.utils.storage import PackageStorage


@pytest.fixture
def storage() -> PackageStorage:
    return PackageStorage()


def test_get_storages(storage: PackageStorage):
    """should return a Gio.Liststore object"""
    assert isinstance(storage.get_storage(), Gio.ListStore)


def test_storage_add_pkg(storage: PackageStorage, pkg):
    """should contain one package added package"""
    storage.add_package(pkg)
    assert len(storage) == 1
    assert storage.get_storage()[0] == pkg


def test_storage_add_pkg_twice(storage: PackageStorage, pkg):
    """should contain one package added package twice"""
    storage.add_package(pkg)
    storage.add_package(pkg)
    assert len(storage) == 1
    assert storage._index == {pkg.nevra: 1}
    assert storage.get_storage()[0] == pkg


def test_storage_add_pkgs(storage: PackageStorage, pkg, pkg_other):
    """should contain two packages added packages"""
    storage.add_packages([pkg, pkg_other])
    assert len(storage) == 2
    assert storage.get_storage()[0] == pkg
    assert storage.get_storage()[1] == pkg_other


def test_storage_contains(storage: PackageStorage, pkg, pkg_other):
    """should be able to check that a package exists using in operator"""
    storage.add_packages([pkg])
    assert pkg in storage
    assert pkg_other not in storage


def test_storage_iterate(storage: PackageStorage, pkg, pkg_other):
    """should be interable over all packages"""
    storage.add_packages([pkg, pkg_other])
    pkgs = list(storage)
    assert pkgs == [pkg, pkg_other]


def test_storage_clear(storage: PackageStorage, pkg, pkg_other):
    """should clear all packages"""

    storage.add_packages([pkg, pkg_other])
    assert len(storage.get_storage()), 2
    current_id = id(storage.get_storage())
    store = storage.clear()
    assert id(store) != current_id
    assert len(storage) == 0


def test_storage_insert_sorted(storage: PackageStorage, pkg, pkg_other):
    """should sort by name"""
    storage.add_package(pkg_other)
    storage.insert_sorted(pkg, lambda a, b: a.name > b.name)
    assert storage.get_storage()[0] == pkg
    assert storage.get_storage()[1] == pkg_other


def test_storage_insert_sorted_illegal(storage: PackageStorage, pkg, pkg_other):
    """should sort by name"""
    storage.add_package(pkg_other)
    with pytest.raises(ValueError):
        storage.insert_sorted("illegal", lambda a, b: a.name > b.name)


def test_storage_sort_name(storage: PackageStorage, pkg, pkg_other):
    """should sort by name"""
    storage.add_packages([pkg_other, pkg])  # otherpkg, mypkg
    storage.sort_by(SortType.NAME)  # mypkg, otherpkg
    assert storage.get_storage()[0] == pkg
    assert storage.get_storage()[1] == pkg_other


def test_storage_sort_name_single(storage: PackageStorage, pkg):
    """should sort by name, with single element"""
    storage.add_package(pkg)  # otherpkg, mypkg
    storage.sort_by(SortType.NAME)  # mypkg, otherpkg
    assert storage.get_storage()[0] == pkg


def test_storage_sort_repo(storage: PackageStorage, pkg, pkg_other):
    """should sort by repo"""
    storage.add_packages([pkg, pkg_other])  # repo2, repo1
    storage.sort_by(SortType.REPO)  # repo1, repo2
    assert storage.get_storage()[0] == pkg_other
    assert storage.get_storage()[1] == pkg


def test_storage_sort_size(storage: PackageStorage, pkg, pkg_other):
    """should sort by size"""
    storage.add_packages([pkg, pkg_other])  # 2048, 1024
    storage.sort_by(SortType.SIZE)  # 1024, 2048
    assert storage.get_storage()[0] == pkg_other
    assert storage.get_storage()[1] == pkg


def test_storage_sort_arch(storage: PackageStorage, pkg, pkg_other):
    """should sort by size"""
    storage.add_packages([pkg, pkg_other])  # x86_64, noarch
    storage.sort_by(SortType.ARCH)  # noarch, x86_64
    assert storage.get_storage()[0] == pkg_other
    assert storage.get_storage()[1] == pkg


def test_storage_sort_illegal(storage: PackageStorage, pkg, pkg_other):
    """should raise ValueError on sort by illegal type"""
    with pytest.raises(ValueError):
        storage.add_packages([pkg, pkg_other])  # x86_64, noarch
        storage.sort_by("notfound")  # noarch, x86_64


def test_storage_add_illegal(storage: PackageStorage, pkg, pkg_other):
    """should raise error on adding illegal datatypes"""
    with pytest.raises(ValueError):
        storage.add_packages([pkg, pkg_other, "illegal"])
    with pytest.raises(ValueError):
        storage.add_packages([pkg, pkg_other, None])


def test_storage_find_by_nevra(storage: PackageStorage, pkg, pkg_other, pkg_upd):
    """should be able to find packages by nevra"""
    storage.add_packages([pkg, pkg_other])  # x86_64, noarch
    po = storage.find_by_nevra(pkg.nevra)  # pkg is in storage
    assert po == pkg
    po = storage.find_by_nevra(pkg_upd.nevra)  # pkg is not in storage
    assert po is None
