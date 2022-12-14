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
from yumex.utils import format_number

from enum import IntEnum


class PackageState(IntEnum):
    UPDATE = 1
    AVAILABLE = 2
    INSTALLED = 3
    DOWNGRADE = 4


class PackageAction(IntEnum):
    DOWNGRADE = 10
    UPGRADE = 20
    INSTALL = 30
    REINSTALL = 40
    ERASE = 50


class YumexPackage(GObject.GObject):
    def __init__(self, pkg, state=PackageState.AVAILABLE, action=0):
        super(YumexPackage, self).__init__()
        self.queued = False
        self.queue_action = False  # package being procced by the queue
        self.name = pkg.name
        self.arch = pkg.arch
        self.epoch = pkg.epoch
        self.release = pkg.release
        self.version = pkg.version
        self.repo = pkg.reponame
        self.description = pkg.summary
        self.sizeB = int(pkg.size)
        self.state = state
        self.is_dep = False
        self.ref_to = None
        self.action = action

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
        return format_number(self.sizeB)

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

    def __eq__(self, other) -> bool:
        return self.nevra == other.nevra


class YumexPackageCache:
    def __init__(self, backend) -> None:
        self._packages = {}
        self.backend = backend
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
                    self.update_state(cached_pkg, pkg)
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

    def update_state(self, current, new):
        """update the state of the cached pkg"""
        match (current.state, new.state):
            case (PackageState.AVAILABLE, PackageState.UPDATE):
                current.state = PackageState.UPDATE
            case (PackageState.INSTALLED, PackageState.UPDATE):
                current.state = PackageState.UPDATE
            case (PackageState.AVAILABLE, PackageState.INSTALLED):
                current.state = PackageState.INSTALLED
