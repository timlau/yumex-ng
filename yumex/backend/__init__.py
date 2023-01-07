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

from gi.repository import GObject
from yumex.utils import format_number
from yumex.utils.enums import PackageAction, PackageState, SearchField  # noqa: F401


class YumexPackage(GObject.GObject):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.name: str = kwargs.pop("name")
        self.arch: str = kwargs.pop("arch")
        self.epoch: str = kwargs.pop("epoch")
        self.release: str = kwargs.pop("release")
        self.version: str = kwargs.pop("version")
        self.repo: str = kwargs.pop("repo")
        self.description: str = kwargs.pop("description")
        self.sizeB: int = kwargs.pop("size")
        self.state: PackageState = kwargs.pop("state", PackageState.AVAILABLE)
        self.action: PackageAction = kwargs.pop("state", PackageAction.NONE)
        self.is_dep: bool = False
        self.ref_to: YumexPackage = None
        self.queued: bool = False
        self.queue_action: bool = False

    @property
    def installed(self) -> bool:
        return self.state == PackageState.INSTALLED

    def set_state(self, state: PackageState) -> None:
        self.state = state

    def set_installed(self) -> None:
        self.repo = f"@{self.repo}"
        self.state = PackageState.INSTALLED

    def set_ref_to(self, pkg, state: PackageState) -> None:
        self.ref_to = pkg
        self.ref_to.state = PackageState.INSTALLED

    @property
    def size(self) -> str:
        return format_number(self.sizeB)

    @property
    def evr(self) -> str:
        if self.epoch:
            return f"{self.epoch}:{self.version}-{self.release}"
        else:
            return f"{self.version}-{self.release}"

    @property
    def nevra(self) -> str:
        return f"{self.name}-{self.evr}.{self.arch}"

    def __repr__(self) -> str:
        return f"YumexPackage({self.nevra} : {self.repo})"

    def __eq__(self, other) -> bool:
        return self.nevra == other.nevra

    def __hash__(self) -> int:
        return hash(self.nevra)

    @property
    def id(self) -> str:
        nevra_r = (
            self.name,
            self.epoch,
            self.version,
            self.release,
            self.arch,
            self.repo[1:],
        )
        return ",".join([str(elem) for elem in nevra_r])
