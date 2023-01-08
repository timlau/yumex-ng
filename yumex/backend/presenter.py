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

from typing import Generator
from yumex.backend.dnf import YumexPackage
from yumex.constants import backend
from yumex.backend.interface import PackageBackend
from yumex.utils import log

if backend == "DNF5":
    from yumex.backend.dnf.dnf5 import Backend as Dnf5Backend
else:
    from yumex.backend.dnf.dnf4 import Backend as Dnf4Backend, DnfCallback

from yumex.ui.progress import YumexProgress

from yumex.utils.enums import PackageFilter, PackageState


class YumexPackageCache:
    """A cache for storing YumexPackages, so the state is preserved when getting packages
    from the PackageBackend.

    Implement the PackageCache protocol class
    """

    def __init__(self, backend: PackageBackend) -> None:
        self._packages = {}
        self.backend: PackageBackend = backend
        self._package_dict = {}

    def get_packages_by_filter(
        self, pkgfilter: PackageFilter, reset=False
    ) -> list[YumexPackage]:
        if pkgfilter not in self._packages or reset:
            pkgs = self.get_packages(self.backend.get_packages(pkgfilter))
            if pkgs is not None:
                self._packages[pkgfilter] = list(pkgs)
            else:
                self._packages[pkgfilter] = []
                log(
                    f" YumexPackageCache: ({__name__}) : no packages found for {pkgfilter}"
                )
        return self._packages[pkgfilter]

    def get_packages(
        self, pkgs: list[YumexPackage]
    ) -> Generator[YumexPackage, None, None]:
        for pkg in pkgs:
            yield self.get_package(pkg)

    def get_package(self, pkg: YumexPackage) -> YumexPackage:
        """cache a new package or return the already cached one"""
        if pkg not in self._package_dict:
            self._package_dict[pkg] = pkg
            return pkg
        else:
            cached_pkg = self._package_dict[pkg]
            if pkg.state != cached_pkg.state:
                log(f" update state : {cached_pkg}{cached_pkg.state} {pkg}{pkg.state}")
                self._update_state(cached_pkg, pkg)
            # use the action from the newest pkg,
            # to get queued deps, sorted the right way
            cached_pkg.action = pkg.action
            return cached_pkg

    def _update_state(self, current, new) -> None:
        """update the state of the cached pkg"""
        match (current.state, new.state):
            case (PackageState.AVAILABLE, PackageState.UPDATE):
                current.state = PackageState.UPDATE
            case (PackageState.INSTALLED, PackageState.UPDATE):
                current.state = PackageState.UPDATE
            case (PackageState.AVAILABLE, PackageState.INSTALLED):
                current.state = PackageState.INSTALLED


class YumexPresenter:
    """presenter class in Model-view-presenter (MVP) architectural pattern

    It works as a middle man between the UI and backend package data, so the UI can work
    diffent package backend in a more generic way.

    The used package backends, implement the PackageBackend protocol methods, so the UI has a well
    defined interface to using the backend without knowledge of packaging API used.

    Implement the Presenter protocol class
    """

    def __init__(self, win) -> None:
        self.win = win
        self._backend: PackageBackend = None
        self._cache: YumexPackageCache = None

    @property
    def backend(self) -> PackageBackend:
        if not self._backend:
            if backend == "DNF5":
                self._backend: PackageBackend = Dnf5Backend(self)
            else:
                callback = DnfCallback(self.win)
                self._backend: PackageBackend = Dnf4Backend(callback=callback)

        return self._backend

    @property
    def package_cache(self) -> YumexPackageCache:
        if not self._cache:
            self._cache: YumexPackageCache = YumexPackageCache(backend=self.backend)
        return self._cache

    @property
    def progress(self) -> YumexProgress:
        return self.win.progress

    def reset_backend(self) -> None:
        del self._backend
        self._backend = None

    def reset_cache(self) -> None:
        del self._cache
        self._cache = None
