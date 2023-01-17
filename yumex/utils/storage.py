from typing import Protocol


from gi.repository import Gio

from yumex.backend.interface import Presenter
from yumex.utils.enums import SortType


class Storage(Protocol):
    def get_storage(self) -> Gio.ListStore:
        ...

    def clear(self) -> None:
        ...

    def add_packages(self, packages: list) -> None:
        ...

    def sort_by(self, attr: SortType) -> None:
        ...


class PackageStorage:
    def __init__(self, cls, presenter: Presenter):
        self._cls = cls
        self.presenter = presenter
        self._store = Gio.ListStore.new(self._cls)

    def __iter__(self):
        return iter(self._store)

    def __next__(self):
        return next(self._store)

    def get_storage(self) -> Gio.ListStore:
        return self._store

    def clear(self) -> Gio.ListStore:
        self._store = Gio.ListStore.new(self._cls)
        return self._store

    def add_packages(self, packages: list) -> None:
        for package in packages:
            self._store.append(package)

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
