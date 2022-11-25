#
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


import os

from gi.repository import Gtk, Adw, Gio

from yumex.constants import rootdir

@Gtk.Template(resource_path=f"{rootdir}/ui/window.ui")
class YumexMainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "YumexMainWindow"

    content = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    content_groups = Gtk.Template.Child("content_groups")
    content_plugins = Gtk.Template.Child("content_queue")
    main_menu = Gtk.Template.Child("main-menu")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)