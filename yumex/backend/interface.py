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
# Copyright (C) 2022  Tim Lauridsen

from typing import Protocol, Union
from gi.repository import Gio

from yumex.backend import YumexPackage
from yumex.ui.progress import YumexProgress

from yumex.utils.enums import PackageFilter, SearchField, InfoType


class PackageCache(Protocol):
    def get_packages_by_filter(self, pkgfilter, reset=False):
        ...

    def add_packages(self, pkgs):
        ...

    def get_package(self, pkg):
        ...


class PackageBackend(Protocol):
    """protocol class for a package backend"""

    def reset_backend(self) -> None:
        ...

    def get_packages(self, pkg_filter: PackageFilter) -> list[YumexPackage]:
        ...

    def search(self, txt: str, field: SearchField) -> list[YumexPackage]:
        ...

    def get_package_info(self, pkg: YumexPackage, attr: InfoType) -> Union[str, None]:
        ...

    def get_repositories(self) -> list[str]:
        ...

    def depsolve(self, store: Gio.ListStore) -> list[YumexPackage]:
        ...


class Presenter(Protocol):
    @property
    def backend(self) -> PackageBackend:
        ...

    @property
    def package_cache(self) -> PackageCache:
        ...

    @property
    def progress(self) -> YumexProgress:
        ...

    def reset_backend(self) -> None:
        ...

    def reset_cache(self) -> None:
        ...
