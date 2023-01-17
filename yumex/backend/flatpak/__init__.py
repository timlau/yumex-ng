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

""" backend for handling flatpaks"""

from gi.repository import Flatpak, GObject

from yumex.utils.types import FlatpakRefString, FlatpakRef
from yumex.utils.enums import FlatpakType, FlatpakLocation


class FlatpakPackage(GObject.GObject):
    """wrapper for a installed flatpak"""

    def __init__(self, ref: FlatpakRef, location: FlatpakLocation, is_update=False):
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
        name = self.ref.get_appdata_name()
        if not name:
            id = self.ref.get_name()
            name = id.split(".")[-1]
            self.log(f"flatpak {id} don't have an appname, using {name}")
        return name

    @property
    def version(self) -> str:
        """return the flatpak version"""
        version = self.ref.get_appdata_version()
        if not version:
            version = ""
        return

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

    def __repr__(self) -> FlatpakRefString:
        """return the ref as string: ex. app/org.gnome.design.Contrast/x86_64/stable"""
        return self.ref.format_ref()
