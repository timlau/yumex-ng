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

import os

from pathlib import Path
from gi.repository import Gtk, Gio, Adw

from yumex.constants import rootdir

from yumex.backend.flatpak import (
    FlatpakBackend,
    FlatpakLocation,
    FlatpakPackage,
    FlatpakType,
)
from yumex.utils import log, RunAsync  # noqa: F401

from yumex.ui.flatpak_installer import YumexFlatpakInstaller


@Gtk.Template(resource_path=f"{rootdir}/ui/flatpak_view.ui")
class YumexFlatpakView(Gtk.ListView):
    __gtype_name__ = "YumexFlatpakView"

    selection = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.win = window
        self.icons_paths = self.get_icon_paths()
        self.reset()

    def reset(self):
        self.store = Gio.ListStore.new(FlatpakPackage)
        self.backend = FlatpakBackend(self.win)
        for elem in self.backend.get_installed(location=FlatpakLocation.BOTH):
            if elem.type == FlatpakType.APP:  # show only apps
                self.store.append(elem)
        self.store.sort(lambda a, b: a.name > b.name)
        self.selection.set_model(self.store)
        self.selection.set_selected(0)

    def get_icon_paths(self):
        return [f"{path}/icons/" for path in os.environ["XDG_DATA_DIRS"].split(":")]

    def find_icon(self, pkg):
        for path in self.icons_paths:
            files = list(Path(f"{path}").rglob(f"{pkg.id}.*"))
            if files:
                return files[0].as_posix()
        return None

    def update_all(self):
        # self.backend.do_update(self.store)
        def completed(deps, error=None):
            self.win.progress.hide()
            self.reset()

        RunAsync(self.backend.do_update_all, completed, self.store)

    def update(self, pkg):
        # self.backend.do_update(self.store)
        def completed(deps, error=None):
            self.win.progress.hide()
            self.reset()

        RunAsync(self.backend.do_update, completed, pkg)

    def install(self, *args):
        """install a new flatpak"""

        def completed(rc, *args):
            self.win.progress.hide()
            # Translator: {id} is variable and should not be changed
            if rc:
                self.win.show_message(_(f"{id} is now installed"), timeout=5)
            self.reset()

        def on_close(*args):
            global id
            id = flatpak_installer.id.get_text()
            source = flatpak_installer.source.get_selected_item().get_string()
            ref = self.backend.find_ref(source, id)
            location = flatpak_installer.location.get_selected_item().get_string()
            if flatpak_installer.confirm:
                RunAsync(self.backend.do_install, completed, ref, source, location)

        self.win.stack.set_visible_child_name("flatpaks")
        flatpak_installer = YumexFlatpakInstaller(self.win)
        remotes = Gtk.StringList.new()
        for remote in self.backend.get_remotes(location=FlatpakLocation.USER):
            remotes.append(remote)
        flatpak_installer.source.set_model(remotes)
        flatpak_installer.set_transient_for(self.win)
        flatpak_installer.connect("close-request", on_close)
        # flatpak_installer.id.set_text("org.xfce.ristretto")
        flatpak_installer.present()

    def remove(self, pkg=None):
        # self.backend.do_update(self.store)
        def completed(rc, error=None):
            self.win.progress.hide()
            # Translator: {selected.id} is variable and should not be changed
            if rc:
                self.win.show_message(_(f"{selected.id} is now removed"), timeout=5)
            self.reset()

        def response(dialog, result, *args):
            if result == "uninstall":
                RunAsync(self.backend.do_remove, completed, selected)

        if pkg:
            selected = pkg
        else:
            selected = self.selection.get_selected_item()
        dialog = Adw.MessageDialog.new(
            self.win,
            _("Uninstall Flatpak"),
            _(f"Do you want to uninstall\n\n{selected.id}"),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("uninstall", _("Uninstall"))
        dialog.set_response_appearance("uninstall", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", response)
        dialog.present()

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

    @Gtk.Template.Callback()
    def on_delete_clicked(self, widget):
        self.view.remove(pkg=self.pkg)

    @Gtk.Template.Callback()
    def on_update_clicked(self, widget):
        self.view.update(self.pkg)
