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

from yumex.backend.interface import PackageBackend
from yumex.backend.dnf5 import Backend as Dnf5Backend
from yumex.backend.dnf import Backend as Dnf4Backend, DnfCallback

from yumex.ui.progress import YumexProgress

from yumex.constants import backend
from yumex.utils.enums import PackageState


class YumexPackageCache:
    def __init__(self, backend: PackageBackend) -> None:
        self._packages = {}
        self.backend: PackageBackend = backend
        self.nerva_dict = {}

    def get_packages_by_filter(self, pkgfilter, reset=False):
        if pkgfilter not in self._packages or reset:
            self._packages[pkgfilter] = list(
                self.add_packages(self.backend.get_packages(pkgfilter))
            )
        return self._packages[pkgfilter]

    def add_packages(self, pkgs):
        for pkg in pkgs:
            if pkg.nevra not in self.nerva_dict:
                self.nerva_dict[pkg.nevra] = pkg
                yield pkg
            else:
                cached_pkg = self.nerva_dict[pkg.nevra]
                if pkg.state != cached_pkg.state:
                    self._update_state(cached_pkg, pkg)
                # use the action from the newest pkg,
                # to get queued deps, sorted the right way
                cached_pkg.action = pkg.action
                yield cached_pkg

    def get_package(self, pkg):
        if pkg.nevra not in self.nerva_dict:
            self.nerva_dict[pkg.nevra] = pkg
            return pkg
        else:
            return self.nerva_dict[pkg.nevra]

    def _update_state(self, current, new):
        """update the state of the cached pkg"""
        match (current.state, new.state):
            case (PackageState.AVAILABLE, PackageState.UPDATE):
                current.state = PackageState.UPDATE
            case (PackageState.INSTALLED, PackageState.UPDATE):
                current.state = PackageState.UPDATE
            case (PackageState.AVAILABLE, PackageState.INSTALLED):
                current.state = PackageState.INSTALLED


class YumexPresenter:
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
