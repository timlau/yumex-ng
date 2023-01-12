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
# Copyright (C) 2023  Tim Lauridsen
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yumex.ui.window import YumexMainWindow

import os

from pathlib import Path
from gi.repository import Gtk, Gio, Adw
from yumex.backend.flatpak import FlatpakPackage
from yumex.backend.flatpak.backend import FlatpakBackend

from yumex.constants import rootdir


from yumex.utils import log, RunAsync  # noqa: F401
from yumex.ui.flatpak_installer import YumexFlatpakInstaller
from yumex.utils.enums import FlatpakLocation, FlatpakType, Page


@Gtk.Template(resource_path=f"{rootdir}/ui/flatpak_view.ui")
class YumexFlatpakView(Gtk.ListView):
    __gtype_name__ = "YumexFlatpakView"

    selection = Gtk.Template.Child()

    def __init__(self, win: YumexMainWindow, **kwargs):
        super().__init__(**kwargs)
        self.win: YumexMainWindow = win
        self.icons_paths = self.get_icon_paths()
        self.reset()

    def reset(self):
        self.store = Gio.ListStore.new(FlatpakPackage)
        self.backend = FlatpakBackend(self.win)
        num_updates = 0
        for elem in self.backend.get_installed(location=FlatpakLocation.BOTH):
            if elem.type == FlatpakType.APP:  # show only apps
                self.store.append(elem)
                if elem.is_update:
                    num_updates += 1
        self.store.sort(lambda a, b: a.name > b.name)
        self.selection.set_model(self.store)
        self.selection.set_selected(0)
        self.win.set_needs_attention(Page.FLATPAKS, num_updates)

    def get_icon_paths(self):
        return [f"{path}/icons/" for path in os.environ["XDG_DATA_DIRS"].split(":")]

    def find_icon(self, pkg):
        for path in self.icons_paths:
            files = list(Path(f"{path}").rglob(f"{pkg.id}.*"))
            if files:
                return files[0].as_posix()
        return None

    def update_all(self):
        def build(refs, error=None):
            if refs:
                confirm = self.win.confirm_flatpak_transaction(refs)
                if confirm:
                    RunAsync(self.backend.do_update, execute, self.store, execute=True)
                    return
            execute(False)

        def execute(state, error=None):
            self.win.progress.hide()
            self.reset()

        RunAsync(self.backend.do_update_all, build, self.store, execute=False)

    def update(self, pkg):
        # self.backend.do_update(self.store)
        def build(refs, error=None):
            if refs:
                confirm = self.win.confirm_flatpak_transaction(refs)
                if confirm:
                    RunAsync(self.backend.do_update, execute, pkg, execute=True)
                    return
            execute(False)

        def execute(state, error=None):
            self.win.progress.hide()
            self.reset()

        RunAsync(self.backend.do_update, build, pkg, execute=False)

    def install(self, *args):
        """install a new flatpak"""

        def build(refs, error=None):
            global id, source, ref, location
            if refs:
                confirm = self.win.confirm_flatpak_transaction(refs)
                if confirm:
                    RunAsync(
                        self.backend.do_install,
                        execute,
                        ref,
                        source,
                        location,
                        execute=True,
                    )
                    return
            execute(False)

        def execute(state, error=None):
            self.win.progress.hide()
            if state:
                self.win.show_message(_(f"{id} is now installed"), timeout=5)
            self.reset()

        def on_close(*args):
            global id, source, ref, location
            id = flatpak_installer.id.get_text()
            source = flatpak_installer.source.get_selected_item().get_string()
            ref = self.backend.find_ref(source, id)
            location = flatpak_installer.location.get_selected_item().get_string()
            if flatpak_installer.confirm:
                RunAsync(
                    self.backend.do_install, build, ref, source, location, execute=False
                )

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
        def build(refs, error=None):
            if refs:
                confirm = self.win.confirm_flatpak_transaction(refs)
                if confirm:
                    RunAsync(self.backend.do_remove, execute, selected, execute=True)
                    return
            execute(False)

        def execute(state, error=None):
            self.win.progress.hide()
            if state:
                self.win.show_message(_(f"{selected.id} is now removed"), timeout=5)
            self.reset()

        if pkg:
            selected = [pkg]
        else:
            selected = [self.selection.get_selected_item()]
        RunAsync(self.backend.do_remove, build, selected, execute=False)

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
