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


import logging
from pathlib import Path

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from yumex.backend.flatpak.backend import FlatpakBackend
from yumex.backend.flatpak.search import AppStreamPackage, AppstreamSearcher
from yumex.backend.presenter import YumexPresenter
from yumex.constants import APP_ID, ROOTDIR
from yumex.utils.enums import FlatpakLocation

logger = logging.getLogger(__name__)


class FoundElem(GObject.GObject):
    def __init__(self, package: AppStreamPackage) -> None:
        super().__init__()
        self.pkg: AppStreamPackage = package

    def __str__(self) -> str:
        return str(self.pkg)


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/flatpak_search.ui")
class YumexFlatpakSearch(Adw.Dialog):
    __gtype_name__ = "YumexFlatpakSearch"

    search_id: Gtk.SearchEntry = Gtk.Template.Child()
    location: Adw.ComboRow = Gtk.Template.Child()
    result_view = Gtk.Template.Child()
    selection = Gtk.Template.Child()
    result_factory = Gtk.Template.Child()
    install: Gtk.Button = Gtk.Template.Child()
    remotes: Gtk.Label = Gtk.Template.Child()

    def __init__(self, presenter: YumexPresenter):
        super().__init__()
        self.presenter = presenter
        self.backend: FlatpakBackend = presenter.flatpak_backend
        self.settings = Gio.Settings.new(APP_ID)
        self.confirm = False
        self._loop = GLib.MainLoop()
        self.search_id.set_key_capture_widget(self)
        self.search_id.grab_focus()
        self.store = Gio.ListStore.new(FoundElem)
        self.selection.set_model(self.store)
        self.app_search = AppstreamSearcher()
        self.setup_location()
        self.install.set_sensitive(False)

    def show_dialog(self, win):
        self.present(win)
        self._loop.run()

    def setup_store(self):
        packages = self.app_search.search("torrent")
        for package in packages:
            logger.debug(str(package))
            self.store.append(FoundElem(package))

    def setup_location(self):
        """set the location bases on the settings"""
        fp_location = FlatpakLocation(self.settings.get_string("fp-location"))
        for ndx, location in enumerate(self.location.get_model()):
            if location.get_string() == fp_location:
                self.location.set_selected(ndx)
        if fp_location == "user":
            self.on_location_selected()

    @Gtk.Template.Callback()
    def on_location_selected(self, *args):
        logger.debug(f"fp_search: location changed : {self.location.get_selected_item().get_string()}")
        self.app_search = AppstreamSearcher()
        fp_location = FlatpakLocation(self.location.get_selected_item().get_string())
        installation = self.backend.get_installation(fp_location)
        self.app_search.add_installation(installation)
        remotes = self.backend.get_remotes(fp_location)
        self.remotes.set_label(", ".join(remotes))
        self.on_search(self.search_id)

    @Gtk.Template.Callback()
    def on_ok_clicked(self, *args):
        """Ok button clicked"""
        self._loop.quit()
        logger.debug("flafpak_search Ok clicked")
        self.confirm = True
        selected: AppStreamPackage = self.selection.get_selected_item().pkg
        logger.debug(f"Selected : {selected.flatpak_bundle}")
        self.close()

    @Gtk.Template.Callback()
    def on_cancel_clicked(self, *args):
        """Cancel buttton clicked"""
        self._loop.quit()
        logger.debug("flafpak_search cancel clicked")
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
        logger.debug(f"(flatpak_seach) key: {key}  location: {location}")
        self._clear()
        packages = self.app_search.search(key)
        if packages:
            self.install.set_sensitive(True)
            for package in packages:
                self.store.append(FoundElem(package))
        else:
            self.install.set_sensitive(False)

    @Gtk.Template.Callback()
    def on_setup(self, widget, item):
        """Setup the widget to show in the Gtk.Listview"""
        row = Row()
        item.set_child(row)

    @Gtk.Template.Callback()
    def on_bind(self, widget, item):
        """bind data from the store object to the widget"""
        row: Row = item.get_child()
        pkg: AppStreamPackage = item.get_item().pkg
        version = pkg.version
        developer = pkg.developer
        if version:
            row.set_title(f"{pkg.name} - {version} - {developer}" if developer else f"{pkg.name} - {version}")
        else:
            row.set_title(f"{pkg.name} - {developer}" if developer else pkg.name)
        summary = GLib.markup_escape_text(pkg.summary)
        row.set_subtitle(summary)
        row.set_tooltip_text(pkg.flatpak_bundle)
        row.repo.set_text(pkg.repo_name)
        row.branch.set_text(pkg.flatpak_bundle.split("/")[-1])
        icon_file = self._get_icon(pkg.id, pkg.repo_name)
        if icon_file:
            row.icon.set_from_file(icon_file)

    def _get_icon(self, id: str, remote_name: str):
        """set the flatpak icon in the ui of current found flatpak"""
        if not remote_name:
            return
        location = FlatpakLocation(self.location.get_selected_item().get_string())
        icon_path = self.backend.get_icon_path(remote_name, location)
        icon_file = Path(f"{icon_path}/{id}.png")
        if icon_file.exists():
            return icon_file.as_posix()


class Row(Adw.ActionRow):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.icon = Gtk.Image().new_from_icon_name("flatpak-symbolic")
        self.icon.set_icon_size(Gtk.IconSize.LARGE)
        self.add_prefix(self.icon)
        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.HORIZONTAL)
        box.props.vexpand = False
        box.props.hexpand = False
        box.props.valign = Gtk.Align.START
        self.branch = Gtk.Label()
        self.branch.add_css_class("tag")
        box.append(self.branch)
        self.repo = Gtk.Label()
        self.repo.add_css_class("tag")
        self.repo.add_css_class("origin")
        box.append(self.repo)
        self.add_suffix(box)
