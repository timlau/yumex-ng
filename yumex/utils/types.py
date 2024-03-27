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

"""Custom types used for type hinting for more clarity"""
from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from yumex.ui.window import YumexMainWindow

import gi

gi.require_version("Flatpak", "1.0")
from gi.repository import Flatpak

# we can not use the YumexMainWindow direct, because of circular imports

MainWindow = Type["YumexMainWindow"]
FlatpakRefString = str  # ex. app/org.gnome.design.Contrast/x86_64/stable
FlatpakRef = Flatpak.Ref
