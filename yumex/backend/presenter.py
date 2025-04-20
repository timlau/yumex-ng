# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2024 Tim Lauridsen

from __future__ import annotations

from typing import Iterable

from yumex.backend.cache import YumexPackageCache
from yumex.backend.dnf import YumexPackage
from yumex.backend.dnf5daemon import YumexRootBackend
from yumex.backend.flatpak.backend import FlatpakBackend
from yumex.backend.interface import (
    PackageBackend,
    PackageCache,
    Progress,
)
from yumex.utils.enums import (
    InfoType,
    PackageFilter,
    Page,
)
from yumex.utils.types import MainWindow


class YumexPresenter:
    """presenter class in Model-view-presenter (MVP) architectural pattern

    It works as a middle man between the UI and backend package data, so the UI can work
    diffent package backend in a more generic way.

    The used package backends, implement the PackageBackend protocol methods, so the UI has a well
    defined interface to using the backend without knowledge of packaging API used.

    Implements Presenter,PackageBackend,PackageCache protocols
    """

    def __init__(self, win: MainWindow) -> None:
        self._win: MainWindow = win
        self._backend: PackageBackend = None
        self._cache: YumexPackageCache = None
        self._fp_backend: FlatpakBackend = None

    @property
    def package_backend(self) -> PackageBackend:
        if not self._backend:
            self._backend: PackageBackend = YumexRootBackend(self)
        return self._backend

    @property
    def package_cache(self) -> PackageCache:
        if not self._cache:
            self._cache: PackageCache = YumexPackageCache(backend=self.package_backend)
        return self._cache

    @property
    def flatpak_backend(self):
        if not self._fp_backend:
            self._fp_backend = FlatpakBackend(self._win)
        return self._fp_backend

    @property
    def progress(self) -> Progress:
        return self._win.progress

    def reset_backend(self) -> None:
        self._backend.reset()

    def reset_flatpak_backend(self) -> None:
        del self._fp_backend
        self._fp_backend = None

    def reset_cache(self) -> None:
        del self._cache
        self._cache = None

    # PackageBackend implementation
    def search(self, txt: str, options: dict) -> list[YumexPackage]:
        return self.package_backend.search(txt, options=options)

    def get_package_info(self, pkg: YumexPackage, attr: InfoType) -> str | None:
        return self.package_backend.get_package_info(pkg, attr)

    def get_repositories(self) -> list[(str, str, bool, int)]:  # id, name, enabled, priority
        return self.package_backend.get_repositories()

    def depsolve(self, pkgs: Iterable[YumexPackage]) -> list[YumexPackage]:
        return self.package_backend.depsolve(pkgs)

    def has_offline_transaction(self) -> bool:
        """Check if there is an offline transaction"""
        return self.package_backend.has_offline_transaction()

    def cancel_offline_transaction(self) -> bool:
        """Cancel the offline transaction"""
        return self.package_backend.cancel_offline_transaction()

    def reboot_and_install(self) -> bool:
        """Reboot and install the system upgrade"""
        return self.package_backend.reboot_and_install()

    # PackageCache protocol implementation
    def get_packages_by_filter(self, pkgfilter: PackageFilter, reset=False) -> list[YumexPackage]:
        return self.package_cache.get_packages_by_filter(pkgfilter, reset)

    def get_packages(self, pkgs: list[YumexPackage]) -> list[YumexPackage]:
        return self.package_cache.get_packages(pkgs)

    def get_package(self, pkg: YumexPackage) -> YumexPackage:
        return self.package_cache.get_package(pkg)

    # Main Window helpers

    def get_main_window(self) -> MainWindow:
        return self._win

    def show_message(self, title, timeout=2):
        self._win.show_message(title, timeout)

    def set_needs_attention(self, page: Page, num: int):
        """set the page needs_attention state"""
        self._win.set_needs_attention(page, num)

    def confirm_flatpak_transaction(self, refs: list) -> bool:
        return self._win.confirm_flatpak_transaction(refs)

    def select_page(self, page: Page):
        self._win.select_page(page)

    def set_window_sesitivity(self, sensitive: bool):
        self._win.set_sesitivity(sensitive)

    def confirm_gpg_import(self, key_values):
        return self._win.confirm_gpg_import(key_values)
