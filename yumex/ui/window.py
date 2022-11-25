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

    content_packages = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    content_groups = Gtk.Template.Child("content_groups")
    content_queue = Gtk.Template.Child("content_queue")
    main_menu = Gtk.Template.Child("main-menu")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_gui()

    def setup_gui(self):
        self.setup_packages()
        self.setup_groups()
        self.setup_queue()
        self.show_message("Welcome to Yum Extender")


    def setup_packages(self):
        self.content_packages.append(self.create_label_center("Packages"))

    def setup_groups(self):
        self.content_groups.append(self.create_label_center("Groups"))

    def setup_queue(self):
        self.content_queue.append(self.create_label_center("Action Queue"))

    def show_message(self, title):
        toast = Adw.Toast(title=title)
        toast.set_timeout(1)
        self.toast_overlay.add_toast(toast)

    def create_label_center(self, label):
        lbl = Gtk.Label()
        lbl.props.hexpand = True
        lbl.props.vexpand = True
        lbl.props.label = label
        return lbl



