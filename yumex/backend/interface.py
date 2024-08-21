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

from typing import Iterable, Protocol, Self

from yumex.backend import TransactionResult
from yumex.backend.dnf import YumexPackage
from yumex.utils.enums import InfoType, PackageFilter, Page, SearchField
from yumex.utils.types import MainWindow


class PackageCache(Protocol):
    """Protocol class for a package cache"""

    def get_packages_by_filter(self, pkgfilter: PackageFilter, reset=False) -> list[YumexPackage]: ...

    def get_packages(self, pkgs: list[YumexPackage]) -> list[YumexPackage]: ...

    def get_package(self, pkg: YumexPackage) -> YumexPackage: ...


class PackageBackend(Protocol):
    """Protocol class for a package backend"""

    def get_packages(self, pkg_filter: PackageFilter) -> list[YumexPackage]: ...

    def search(self, txt: str, field: SearchField, limit: int) -> list[YumexPackage]: ...

    def get_package_info(self, pkg: YumexPackage, attr: InfoType) -> str | None: ...

    def get_repositories(self) -> list[str]: ...

    def depsolve(self, pkgs: Iterable[YumexPackage]) -> list[YumexPackage]: ...


class PackageRootBackend(Protocol):
    """Protocol class for a package root backend"""

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None: ...

    def build_transaction(self, pkgs: list[YumexPackage]) -> TransactionResult: ...

    def run_transaction(self) -> TransactionResult: ...


class BackendFactory(Protocol):
    def get_factory(self) -> PackageBackend: ...


class Progress(Protocol):
    def show(self) -> None: ...

    def hide(self) -> None: ...

    def set_title(self, title: str) -> None: ...

    def set_subtitle(self, title: str) -> None: ...

    def set_progress(self, frac: float) -> None: ...


class Presenter(Protocol):
    """Protocol class for a presenter in  a Model-view-presenter (MVP) architectural pattern"""

    @property
    def progress(self) -> Progress: ...

    def reset_backend(self) -> None: ...

    def reset_cache(self) -> None: ...

    def get_main_window(self) -> MainWindow: ...

    def show_message(self, title, timeout=2) -> None: ...

    def set_needs_attention(self, page: Page, num: int) -> None: ...

    def confirm_flatpak_transaction(self, refs: list) -> bool: ...

    def select_page(self, page: Page) -> None: ...

    def set_window_sesitivity(self, sensitive: bool): ...
