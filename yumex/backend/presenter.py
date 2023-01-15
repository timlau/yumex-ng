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

from yumex.backend.cache import YumexPackageCache
from yumex.constants import backend
from yumex.backend.interface import PackageBackend, PackageCache, Progress

if backend == "DNF5":
    from yumex.backend.dnf.dnf5 import Backend as Dnf5Backend
else:
    from yumex.backend.dnf.dnf4 import Backend as Dnf4Backend, DnfCallback


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
    def package_cache(self) -> PackageCache:
        if not self._cache:
            self._cache: PackageCache = YumexPackageCache(backend=self.backend)
        return self._cache

    @property
    def progress(self) -> Progress:
        return self.win.progress

    def reset_backend(self) -> None:
        del self._backend
        self._backend = None

    def reset_cache(self) -> None:
        del self._cache
        self._cache = None
