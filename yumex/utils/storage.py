from gi.repository import Gio
from yumex.backend.dnf import YumexPackage

from yumex.utils.enums import SortType


class PackageStorage:
    def __init__(self, cls):
        self._cls = cls
        self._store = None
        self.clear()

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def get_storage(self) -> Gio.ListStore:
        return self._store

    def clear(self) -> Gio.ListStore:
        self._store = Gio.ListStore.new(self._cls)
        return self._store

    def add_packages(self, packages: list[YumexPackage]) -> None:
        for package in packages:
            self.add_package(package)

    def add_package(self, package: YumexPackage) -> None:
        if isinstance(package, self._cls):
            self._store.append(package)
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
