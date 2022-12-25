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

import os

from pathlib import Path
from gi.repository import Gtk, Gio, Adw

from yumex.constants import rootdir

from yumex.backend.flatpak import (
    FlatpakBackend,
    FlatpakPackage,
    FlatpakType,
)  # noqa: F401


@Gtk.Template(resource_path=f"{rootdir}/ui/flatpak_view.ui")
class YumexFlatpakView(Gtk.ListView):
    __gtype_name__ = "YumexFlatpakView"

    selection = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.win = window
        self.store = Gio.ListStore.new(FlatpakPackage)
        self.selection.set_model(self.store)
        self.backend = FlatpakBackend()
        self.icons_paths = self.get_icon_paths()
        for elem in self.backend.get_installed(user=True):
            if elem.type == FlatpakType.APP:  # show only apps
                self.store.append(elem)

    def get_icon_paths(self):
        return [f"{path}/icons/" for path in os.environ["XDG_DATA_DIRS"].split(":")]

    def find_icon(self, pkg):
        for path in self.icons_paths:
            files = list(Path(f"{path}").rglob(f"{pkg.id}.*"))
            if files:
                return files[0].as_posix()
        return None

    @Gtk.Template.Callback()
    def on_row_setup(self, widget, item):
        row = YumexFlatpakRow(self)
        item.set_child(row)

    @Gtk.Template.Callback()
    def on_row_bind(self, widget, item):
        row = item.get_child()
        pkg: FlatpakPackage = item.get_item()
        row.pkg = pkg
        icon_file = self.find_icon(pkg)
        if icon_file:
            row.icon.set_from_file(icon_file)
        row.user.set_label(pkg.location)
        row.origin.set_label(pkg.origin)
        row.update.set_visible(pkg.is_update)
        row.set_title(f"{pkg.name} - {pkg.version}")
        row.set_subtitle(pkg.summary)


@Gtk.Template(resource_path=f"{rootdir}/ui/flatpak_row.ui")
class YumexFlatpakRow(Adw.ActionRow):
    __gtype_name__ = "YumexFlatpakRow"

    icon = Gtk.Template.Child()
    user = Gtk.Template.Child()
    update = Gtk.Template.Child()
    origin = Gtk.Template.Child()

    def __init__(self, view, **kwargs):
        super().__init__(**kwargs)
        self.view: YumexFlatpakView = view
        self.pkg: FlatpakPackage = None
