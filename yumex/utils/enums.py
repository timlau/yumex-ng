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

from enum import IntEnum, StrEnum, auto


class PackageState(IntEnum):
    UPDATE = 1
    AVAILABLE = 2
    INSTALLED = 3
    DOWNGRADE = 4


class PackageAction(IntEnum):
    NONE = 0
    DOWNGRADE = 10
    UPGRADE = 20
    INSTALL = 30
    REINSTALL = 40
    ERASE = 50


class SearchField(StrEnum):
    NAME = auto()
    ARCH = auto()
    REPONAME = auto()


class PackageFilter(StrEnum):
    INSTALLED = auto()
    UPDATES = auto()
    AVAILABLE = auto()
    ALL = AVAILABLE
    SEARCH = auto()


# ["description", "files", "update_info"]
class InfoType(StrEnum):
    DESCRIPTION = auto()
    FILES = auto()
    UPDATE_INFO = auto()


# ["name", "arch", "size", "repo"]
class SortType(StrEnum):
    NAME = auto()
    ARCH = auto()
    SIZE = auto()
    REPO = auto()
