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
#

""" backend for handling flatpak"""
import gi

gi.require_version("Flatpak", "1.0")

from enum import IntEnum  # noqa : E402
from gi.repository import Flatpak, GObject  # noqa : E402


class FlatpakType(IntEnum):
    APP = 1
    RUNTIME = 2
    LOCALE = 3
    DEBUG = 4


class FlatpakPackage(GObject.GObject):
    """wrapper for a"""

    def __init__(self, ref, is_user=True):
        super(FlatpakPackage, self).__init__()
        self.ref = ref
        self.is_user = is_user

    @property
    def name(self):
        return self.ref.get_appdata_name()

    @property
    def location(self):
        if self.is_user:
            return "user"
        else:
            return "system"

    @property
    def version(self):
        return self.ref.get_appdata_version()

    @property
    def summary(self):
        return self.ref.get_appdata_summary()

    @property
    def origin(self):
        return self.ref.get_origin()

    @property
    def id(self):
        return self.ref.get_name()

    @property
    def type(self):
        ref_kind = self.ref.get_kind()
        match ref_kind:
            case Flatpak.RefKind.APP:
                pak_type = FlatpakType.APP
            case Flatpak.RefKind.RUNTIME:
                pak_type = FlatpakType.RUNTIME
                if self.id.endswith(".Locale"):
                    pak_type = FlatpakType.LOCALE
        return pak_type

    def __repr__(self) -> str:
        return self.ref.format_ref()


class FlatpakBackend:
    def __init__(self):
        self.user = Flatpak.Installation.new_user()
        self.system = Flatpak.Installation.new_system()

    def get_installed(self, user=True, system=True):
        refs = []
        if user:
            refs += [FlatpakPackage(ref) for ref in self.user.list_installed_refs()]
        if system:
            refs += [
                FlatpakPackage(ref, is_user=False)
                for ref in self.system.list_installed_refs()
            ]
        return refs
