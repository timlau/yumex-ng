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

"""backend for handling flatpaks"""

from enum import Enum, auto

from gi.repository import Flatpak, GObject

from yumex.utils.enums import FlatpakLocation, FlatpakType
from yumex.utils.types import FlatpakRef, FlatpakRefString


class FlatpakUpdate(Enum):
    NO = auto()
    UPDATE = auto()
    EOL = auto()


class FlatpakPackage(GObject.GObject):
    """wrapper for a installed flatpak"""

    def __init__(
        self,
        ref: FlatpakRef,
        location: FlatpakLocation,
        is_update: FlatpakUpdate = FlatpakUpdate.NO,
    ):
        super().__init__()
        self.ref: FlatpakRef = ref
        self.is_update = is_update
        self.location = location

    @property
    def is_user(self) -> bool:
        """return if the flatpak is installed in user context"""
        return self.location == FlatpakLocation.USER

    @property
    def name(self) -> str:
        """return the application name (not id) : ex. Contrast"""
        return self.get_name()

    @property
    def sort_key(self):
        match self.type:
            case FlatpakType.APP:
                return f"0{self.name}"
            case FlatpakType.RUNTIME:
                return f"1{self.name}"
            case FlatpakType.LOCALE:
                return f"2{self.name}"
            case _:
                return f"3{self.name}"

    @property
    def version(self) -> str:
        """return the flatpak version"""
        version = self.ref.get_appdata_version()
        if not version:
            version = ""
        return version

    @property
    def summary(self) -> str:
        """return the flatpak summary"""
        summary = self.ref.get_appdata_summary()
        if not summary:
            summary = ""
        return summary

    @property
    def origin(self) -> str:
        """return the origin remote"""
        return self.ref.get_origin()

    @property
    def id(self) -> str:
        """return the name/id: ex. org.gnome.design.Contrast"""
        return self.ref.get_name()

    @property
    def type(self) -> FlatpakType:
        """the ref type as Enum (runtime/app/locale)"""
        ref_kind = self.ref.get_kind()
        pak_type = FlatpakType.APP
        match ref_kind:
            case Flatpak.RefKind.RUNTIME:
                pak_type = FlatpakType.RUNTIME
                if self.id.endswith(".Locale"):
                    pak_type = FlatpakType.LOCALE
        return pak_type

    def name_from_id(self):
        id = self.ref.get_name()
        ids = id.split(".")
        match self.type:
            case FlatpakType.APP:
                return ids[-1]
            case FlatpakType.RUNTIME:
                return ids[-1]
            case FlatpakType.LOCALE:
                return ids[-2]
            case _:
                return id

    def get_name(self):
        name = self.ref.get_appdata_name()
        if not name:
            name = self.name_from_id()
        match self.type:
            case FlatpakType.APP:
                return name
            case FlatpakType.RUNTIME:
                return f"Runtime: {name}"
            case FlatpakType.LOCALE:
                return f"Locale: {name}"
            case _:
                return f"Other: {name}"

    def __repr__(self) -> FlatpakRefString:
        """return the ref as string: ex. app/org.gnome.design.Contrast/x86_64/stable"""
        return self.ref.format_ref()
