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
# Copyright (C) 2023  Tim Lauridsen

from typing import Iterable, Protocol

from yumex.backend.dnf import YumexPackage

from yumex.utils.enums import PackageFilter, SearchField, InfoType


class PackageCache(Protocol):
    """Protocol class for a package cache"""

    def get_packages_by_filter(
        self, pkgfilter: PackageFilter, reset=False
    ) -> list[YumexPackage]:
        ...

    def get_packages(self, pkgs: list[YumexPackage]) -> list[YumexPackage]:
        ...

    def get_package(self, pkg: YumexPackage) -> YumexPackage:
        ...


class PackageBackend(Protocol):
    """Protocol class for a package backend"""

    def reset_backend(self) -> None:
        ...

    def get_packages(self, pkg_filter: PackageFilter) -> list[YumexPackage]:
        ...

    def search(self, txt: str, field: SearchField, limit: int) -> list[YumexPackage]:
        ...

    def get_package_info(self, pkg: YumexPackage, attr: InfoType) -> str | None:
        ...

    def get_repositories(self) -> list[str]:
        ...

    def depsolve(self, pkgs: Iterable[YumexPackage]) -> list[YumexPackage]:
        ...


class Progress(Protocol):
    def show(self) -> None:
        ...

    def hide(self) -> None:
        ...

    def set_title(self, title: str) -> None:
        ...

    def set_subtitle(self, title: str) -> None:
        ...

    def set_progress(self, frac: float) -> None:
        ...


class Presenter(Protocol):
    """Protocol class for a presenter in  a Model-view-presenter (MVP) architectural pattern"""

    @property
    def backend(self) -> PackageBackend:
        ...

    @property
    def package_cache(self) -> PackageCache:
        ...

    @property
    def progress(self) -> Progress:
        ...

    def reset_backend(self) -> None:
        ...

    def reset_cache(self) -> None:
        ...
