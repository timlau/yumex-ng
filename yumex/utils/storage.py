import logging

from gi.repository import Gio

from yumex.backend.dnf import YumexPackage
from yumex.utils.enums import SortType

logger = logging.getLogger(__name__)


class PackageStorage:
    """A wrapper for a Gio.ListStore with YumexPackage objects"""

    def __init__(self):
        self._store: Gio.ListStore = None
        self._index: dict = {}
        self.clear()

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __contains__(self, item):
        return item.nevra in self._index

    def get_storage(self) -> Gio.ListStore:
        return self._store

    def clear(self) -> Gio.ListStore:
        self._store = Gio.ListStore.new(YumexPackage)
        self._index = {}
        return self._store

    def add_packages(self, packages: list[YumexPackage]) -> None:
        for package in packages:
            self.add_package(package)

    def add_package(self, package: YumexPackage) -> None:
        if isinstance(package, YumexPackage):
            if package.nevra in self._index:
                logger.debug(f"Package {package} already exists in storage")
            else:
                self._store.append(package)
                self._index[package.nevra] = 1
        else:
            raise ValueError(f"Can't add {package} to package storage")

    def insert_sorted(self, package: YumexPackage, sort_fn: callable) -> None:
        if isinstance(package, YumexPackage):
            if package.nevra in self._index:
                logger.debug(f"Package {package} already exists in storage")
            else:
                self._store.insert_sorted(package, sort_fn)
                self._index[package.nevra] = 1
        else:
            raise ValueError(f"Can't add {package} to package storage")

    def sort_by(self, attr: SortType) -> Gio.ListStore:
        match attr:
            case SortType.NAME:
                self._store.sort(lambda a, b: a.name.lower() > b.name.lower())
            case SortType.ARCH:
                self._store.sort(lambda a, b: a.arch > b.arch)
            case SortType.SIZE:
                self._store.sort(lambda a, b: a.size > b.size)
            case SortType.REPO:
                self._store.sort(lambda a, b: a.repo > b.repo)
            case other:
                raise ValueError(f"Unknown sort type: {other}")
        return self._store

    def find_by_nevra(self, nevra: str) -> YumexPackage | None:
        return next((pkg for pkg in self._store if pkg.nevra == nevra), None)
