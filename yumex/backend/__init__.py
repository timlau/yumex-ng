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
#
# Copyright (C) 2022  Tim Lauridsen
#
#

from gi.repository import GObject

from enum import IntEnum


class PackageState(IntEnum):
    UPDATE = 1
    AVAILABLE = 2
    INSTALLED = 3


class YumexPackage(GObject.GObject):
    def __init__(self, pkg, state=PackageState.AVAILABLE):
        super(YumexPackage, self).__init__()
        self.queued = False
        self.name = pkg.name
        self.arch = pkg.arch
        self.epoch = pkg.epoch
        self.release = pkg.release
        self.version = pkg.version
        self.repo = pkg.reponame
        self.description = pkg.summary
        self.sizeB = pkg.size
        self.state = state
        self.ref_to = None

    def set_installed(self):
        self.repo = f"@{self.repo}"
        self.installed = True
        self.state = PackageState.INSTALLED

    def set_update(self, inst_pkg):
        self.ref_to = YumexPackage(inst_pkg)
        self.ref_to.state = PackageState.INSTALLED
        self.state = PackageState.UPDATE

    @property
    def size(self):
        return str(self.sizeB)

    @property
    def styles(self):
        match self.state:
            case PackageState.INSTALLED:
                return ["success"]
            case PackageState.UPDATE:
                return ["error"]
        return []

    @property
    def evr(self):
        if self.epoch:
            return f"{self.epoch}:{self.version}-{self.release}"
        else:
            return f"{self.version}-{self.release}"

    @property
    def nevra(self):
        return f"{self.name}-{self.evr}.{self.arch}"

    def __repr__(self) -> str:
        return f"{self.nevra} : {self.repo}"


class YumexPackageCache:
    def __init__(self, backend) -> None:
        self._packages = {}
        self.backend = backend

    def get_packages(self, pkgfilter, reset=False):
        if pkgfilter not in self._packages or reset:
            self._packages[pkgfilter] = self.backend.get_packages(pkgfilter)
        return self._packages[pkgfilter]
