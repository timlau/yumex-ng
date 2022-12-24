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
        for elem in self.backend.get_installed(user=True):
            if elem.type == FlatpakType.APP:  # show only apps
                self.store.append(elem)

    @Gtk.Template.Callback()
    def on_row_setup(self, widget, item):
        row = Adw.ActionRow()
        item.set_child(row)

    @Gtk.Template.Callback()
    def on_row_bind(self, widget, item):
        row = item.get_child()
        pkg = item.get_item()
        row.set_title(pkg.name)
        row.set_subtitle(pkg.summary)
