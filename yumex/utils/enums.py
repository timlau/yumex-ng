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

from enum import Enum, IntEnum, StrEnum, auto


class FlatpakAction(IntEnum):
    UPDATE = auto()
    INSTALL = auto()
    UNINSTALL = auto()


class FlatpakType(IntEnum):
    """flatpak type"""

    APP = 1
    RUNTIME = 2
    LOCALE = 3
    DEBUG = 4


class PackageTodo(IntEnum):
    """Package todo action"""

    NONE = 0
    INSTALL = 1
    REMOVE = 2
    UPDATE = 3
    REINSTALL = 4
    DOWNGRADE = 5
    DISTROSYNC = 6


class FlatpakLocation(StrEnum):
    """flatpak install location"""

    USER = auto()
    SYSTEM = auto()
    BOTH = auto()  # used only as a filter, where we want both locations


class Page(StrEnum):
    PACKAGES = auto()
    FLATPAKS = auto()
    QUEUE = auto()
    GROUPS = auto()


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


# definded in include/libdnf5/rpm/transaction_callbacks.hpp (dnf5)
class ScriptType(IntEnum):
    UNKNOWN = 0
    PRE_INSTALL = 1  # "%pre"
    POST_INSTALL = 2  # "%post"
    PRE_UNINSTALL = 3  # "%preun"
    POST_UNINSTALL = 4  # "%postun"
    PRE_TRANSACTION = 5  # "%pretrans"
    POST_TRANSACTION = 6  # "%posttrans"
    TRIGGER_PRE_INSTALL = 7  # "%triggerprein"
    TRIGGER_INSTALL = 8  # "%triggerin"
    TRIGGER_UNINSTALL = 9  # "%triggerun"
    TRIGGER_POST_UNINSTALL = 10  # "%triggerpostun"
    SYSUSERS = 11  # sysusers.d integration
    PREUN_TRANSACTION = 12  # "%preuntrans"
    POSTUN_TRANSACTION = 13  # "%postuntrans"

    def __str__(self):
        return str(self.name).title().replace("_", "")


# defined in include/libdnf5/transaction/transaction_item_action.hpp in dnf5 code
class TransactionAction(IntEnum):
    INSTALL = 1
    UPGRADE = 2
    DOWNGRADE = 3
    REINSTALL = 4
    REMOVE = 5
    REPLACED = 6
    REASON_CHANGE = 7
    ENABLE = 8
    DISABLE = 9
    RESET = 10


class TransactionCommand(Enum):
    NONE = auto()
    SYSTEM_UPGRADE = auto()
    IS_FILE = auto()
    SYSTEM_DISTRO_SYNC = auto()


class DownloadType(Enum):
    REPO = auto()
    PACKAGE = auto()
    UNKNOWN = auto()


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
