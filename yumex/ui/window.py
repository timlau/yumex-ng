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

from gi.repository import Gtk, Adw, Gio

from yumex.constants import rootdir, app_id
from yumex.ui.package_row import YumexPackageRow


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

        self.settings = Gio.Settings(app_id)

        self.connect("unrealize", self.save_window_props)

        self.setup_gui()

    def save_window_props(self, *args):
        win_size = self.get_default_size()

        self.settings.set_int("window-width", win_size.width)
        self.settings.set_int("window-height", win_size.height)

        self.settings.set_boolean("window-maximized", self.is_maximized())
        self.settings.set_boolean("window-fullscreen", self.is_fullscreen())

    def setup_gui(self):
        self.setup_packages()
        self.setup_groups()
        self.setup_queue()

    def setup_packages(self):
        # self.content_packages.append(self.create_label_center("Packages"))
        pkg = YumexPackageRow("packagename 1", "this is a package",installed=True)
        self.content_packages.append(pkg)
        pkg = YumexPackageRow("packagename 2", "this is a package",repo="Updates")
        self.content_packages.append(pkg)
        pkg = YumexPackageRow("packagename 3", "this is a package",installed=True)
        self.content_packages.append(pkg)
        pkg = YumexPackageRow("packagename 4", "this is a package",version="12.23.4-34")
        self.content_packages.append(pkg)
        pkg = YumexPackageRow("packagename 5", "this is a package")
        self.content_packages.append(pkg)

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
        lbl.add_css_class("my_label")
        lbl.add_css_class("accent")
        return lbl

    @Gtk.Template.Callback()
    def on_apply_actions_clicked(self, *_args):
        self.show_message("Apply pressed")
