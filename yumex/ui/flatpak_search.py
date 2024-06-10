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


from gi.repository import Gtk, Adw, GLib, Gio, GObject

from yumex.backend.flatpak.backend import FlatpakBackend
from yumex.backend.flatpak.search import AppStreamPackage, AppstreamSearcher
from yumex.backend.presenter import YumexPresenter
from yumex.utils.enums import FlatpakLocation
from yumex.constants import APP_ID, ROOTDIR
from yumex.utils import log


class FoundElem(GObject.GObject):
    def __init__(self, package: AppStreamPackage) -> None:
        super().__init__()
        self.pkg: AppStreamPackage = package

    def __str__(self) -> str:
        return str(self.pkg)


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/flatpak_search.ui")
class YumexFlatpakSearch(Adw.Window):
    __gtype_name__ = "YumexFlatpakSearch"

    search_id: Gtk.SearchEntry = Gtk.Template.Child()
    location: Adw.ComboRow = Gtk.Template.Child()
    result_view = Gtk.Template.Child()
    selection = Gtk.Template.Child()
    result_factory = Gtk.Template.Child()

    def __init__(self, presenter: YumexPresenter):
        super().__init__()
        self.presenter = presenter
        self.backend: FlatpakBackend = presenter.flatpak_backend
        self.settings = Gio.Settings(APP_ID)
        self.confirm = False
        self._loop = GLib.MainLoop()
        self.search_id.set_key_capture_widget(self)
        self.search_id.grab_focus()
        self.result_factory.connect("setup", self.on_setup)
        self.result_factory.connect("bind", self.on_bind)
        self.store = Gio.ListStore.new(FoundElem)
        self.selection.set_model(self.store)
        self.app_search = AppstreamSearcher()
        self.app_search.add_installation(self.backend.user)

    def show(self):
        self.present()
        self._loop.run()

    def setup_store(self):
        packages = self.app_search.search("torrent")
        for package in packages:
            log(str(package))
            self.store.append(FoundElem(package))

    def setup_location(self):
        """set the location bases on the settings"""
        fp_location = FlatpakLocation(self.settings.get_string("fp-location"))
        for ndx, location in enumerate(self.location.get_model()):
            if location.get_string() == fp_location:
                self.location.set_selected(ndx)

    @Gtk.Template.Callback()
    def on_ok_clicked(self, *args):
        """Ok button clicked"""
        self._loop.quit()
        log("flafpak_search Ok clicked")
        self.confirm = True
        selected: AppStreamPackage = self.selection.get_selected_item().pkg
        log(f"Selected : {selected.flatpak_bundle}")
        self.close()

    @Gtk.Template.Callback()
    def on_cancel_clicked(self, *args):
        """Cancel buttton clicked"""
        self._loop.quit()
        log("flafpak_search cancel clicked")
        self.close()

    def _clear(self) -> None:
        """clear all search related, used when nothing is found"""
        self.store = Gio.ListStore.new(FoundElem)
        self.selection.set_model(self.store)

    @Gtk.Template.Callback()
    def on_search(self, widget):
        """typeahead search handler"""
        key = widget.get_text()
        if key == "" or len(key) < 3:
            self._clear()
            return
        location = FlatpakLocation(self.location.get_selected_item().get_string())
        log(f"(flatpak_seach) key: {key}  location: {location}")
        self.store = Gio.ListStore.new(FoundElem)
        self.selection.set_model(self.store)
        packages = self.app_search.search(key)
        for package in packages:
            self.store.append(FoundElem(package))

    # @Gtk.Template.Callback()
    def on_setup(self, widget, item):
        """Setup the widget to show in the Gtk.Listview"""
        label = Gtk.Label()
        label.set_xalign(0.0)
        item.set_child(label)

    # @Gtk.Template.Callback()
    def on_bind(self, widget, item):
        """bind data from the store object to the widget"""
        label = item.get_child()
        obj: FoundElem = item.get_item()
        label.set_text(str(obj))
