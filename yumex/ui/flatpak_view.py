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
from typing import TYPE_CHECKING, Callable

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

    def __init__(self, win, **kwargs) -> None:
        super().__init__(**kwargs)
        self.win: YumexMainWindow = win
        self.icons_paths = self.get_icon_paths()
        self.reset()

    def reset(self) -> None:
        """Create a new store and populate with flatpak fron the backend"""
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

    def get_icon_paths(self) -> list[str]:
        """list of possible icon location for installed flatpaks"""
        return [f"{path}/icons/" for path in os.environ["XDG_DATA_DIRS"].split(":")]

    def find_icon(self, pkg: FlatpakPackage) -> str | None:
        """find icon file for an installed flatpak"""
        for path in self.icons_paths:
            files = list(Path(f"{path}").rglob(f"{pkg.id}.*"))
            if files:
                return files[0].as_posix()
        return None

    def update_all(self) -> None:
        """update all flatpaks with pending updates"""

        def callback(state, error=None) -> None:
            pass

        self.do_transaction(self.backend.do_update_all, callback, self.store)

    def update(self, pkg) -> None:
        """update a flatpak"""

        def callback(state, error=None) -> None:
            pass

        self.do_transaction(self.backend.do_update, callback, pkg)

    def install(self, *args) -> None:
        """install a new flatpak"""

        def callback(state, error=None) -> None:
            if state:
                self.win.show_message(_(f"{id} is now installed"), timeout=5)

        def on_close(*args) -> None:
            global id, source, ref, location
            id = flatpak_installer.id.get_text()
            source = flatpak_installer.source.get_selected_item().get_string()
            ref = self.backend.find_ref(source, id)
            location = flatpak_installer.location.get_selected_item().get_string()
            if flatpak_installer.confirm:
                self.do_transaction(
                    self.backend.do_install, callback, ref, source, location
                )

        self.win.stack.set_visible_child_name("flatpaks")
        # TODO: make and sync edition of the flatpak installer, to make code more readable
        flatpak_installer = YumexFlatpakInstaller(self.win)
        remotes = Gtk.StringList.new()
        for remote in self.backend.get_remotes(location=FlatpakLocation.USER):
            remotes.append(remote)
        flatpak_installer.source.set_model(remotes)
        flatpak_installer.set_transient_for(self.win)
        flatpak_installer.connect("close-request", on_close)
        flatpak_installer.present()

    def remove(self, pkg=None) -> None:
        """remove an flatpak"""

        def callback(state, error=None) -> None:
            if state:
                self.win.show_message(_(f"{selected[0].id} is now removed"), timeout=5)

        if pkg:
            selected = [pkg]
        else:
            selected = [self.selection.get_selected_item()]
        self.do_transaction(self.backend.do_remove, callback, selected)

    def do_transaction(self, method: Callable, callback: Callable, *args) -> None:
        """Excute the transaction in two runs

        The first get the refs in the transaction and show a confirmation dialog
        The second exceute the transaction

        They run async in a thread and callbacks is called after each run

        The provided callback will be called, with the state of second run
        """

        def first_run_callback(refs, error=None) -> None:
            """callback for first run is completed.

            Getting flatpaks in the transaction
            """
            if refs:
                confirm = self.win.confirm_flatpak_transaction(refs)
                if confirm:
                    # Second run
                    RunAsync(method, second_run_callback, *args, execute=True)
                    return
            second_run_callback(False)

        def second_run_callback(state, error=None) -> None:
            """callback for second run is completed.

            Transaction is completted
            """
            self.win.progress.hide()
            self.reset()
            if callback:
                callback(state)

        # First run
        RunAsync(method, first_run_callback, *args, execute=False)

    @Gtk.Template.Callback()
    def on_row_setup(self, widget, item) -> None:
        """Setup row widgets"""
        row = YumexFlatpakRow(self)
        item.set_child(row)

    @Gtk.Template.Callback()
    def on_row_bind(self, widget, item) -> None:
        """bind row data to row widgets"""
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
    """Row widget to show a flatpak"""

    __gtype_name__ = "YumexFlatpakRow"

    icon = Gtk.Template.Child()
    user = Gtk.Template.Child()
    update = Gtk.Template.Child()
    origin = Gtk.Template.Child()

    def __init__(self, view, **kwargs) -> None:
        super().__init__(**kwargs)
        self.view: YumexFlatpakView = view
        self.pkg: FlatpakPackage = None

    @Gtk.Template.Callback()
    def on_delete_clicked(self, widget) -> None:
        self.view.remove(pkg=self.pkg)

    @Gtk.Template.Callback()
    def on_update_clicked(self, widget) -> None:
        self.view.update(self.pkg)
