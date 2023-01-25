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


from pathlib import Path
from gi.repository import Gtk, Adw, GLib, Gio

from yumex.backend.flatpak.backend import FlatpakBackend
from yumex.backend.presenter import YumexPresenter
from yumex.utils.enums import FlatpakLocation
from yumex.constants import APP_ID, ROOTDIR
from yumex.utils import log


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/flatpak_installer.ui")
class YumexFlatpakInstaller(Adw.Window):
    __gtype_name__ = "YumexFlatpakInstaller"

    search_id: Gtk.SearchEntry = Gtk.Template.Child()
    current_id: Adw.ActionRow = Gtk.Template.Child()
    remote: Adw.ComboRow = Gtk.Template.Child()
    location: Adw.ComboRow = Gtk.Template.Child()
    icon: Gtk.Image = Gtk.Template.Child()
    found_num: Gtk.Label = Gtk.Template.Child()

    def __init__(self, presenter: YumexPresenter):
        super().__init__()
        self.presenter = presenter
        self.backend: FlatpakBackend = presenter.flatpak_backend
        self.settings = Gio.Settings(APP_ID)
        self.confirm = False
        self.found_ids: list[str] = []
        self.found_ndx: int = 0
        self._loop = GLib.MainLoop()
        self.setup_location()
        self.read_clipboard()
        self.search_id.set_key_capture_widget(self)
        self.search_id.grab_focus()
        self.icon.set_from_icon_name("flatpak-symbolic")

    def show(self):
        self.present()
        self._loop.run()

    def setup_location(self):
        fp_location = FlatpakLocation(self.settings.get_string("fp-location"))
        for ndx, location in enumerate(self.location.get_model()):
            if location.get_string() == fp_location:
                self.location.set_selected(ndx)

    def read_clipboard(self):
        """If the the clipboard contains

        flatpak install flathub <some id>

        then use these values
        """

        def callback(obj, res, *args):
            try:
                text = clb.read_text_finish(res)
            except GLib.GError:  # type:ignore
                log("cant read from clipboard")
                return

            if text and text.startswith("flatpak install"):
                words = text.split(" ")
                self.search_id.set_text(words[3])
                for ndx, remote in enumerate(self.remote.get_model()):
                    if remote.get_string() == words[2]:
                        self.remote.set_selected(ndx)
            else:
                fp_remote = self.settings.get_string("fp-remote")
                for ndx, remote in enumerate(self.remote.get_model()):
                    if remote.get_string() == fp_remote:
                        self.remote.set_selected(ndx)

        clb = self.get_clipboard()
        try:
            clb.read_text_async(None, callback)
        except GLib.GError:  # type:ignore
            log("cant read from clipboard")

    @Gtk.Template.Callback()
    def on_ok_clicked(self, *args):
        self._loop.quit()
        log("flafpak_installer Ok clicked")
        self.confirm = True
        self.close()

    @Gtk.Template.Callback()
    def on_cancel_clicked(self, *args):
        self._loop.quit()
        log("flafpak_installer cancel clicked")
        self.close()

    @Gtk.Template.Callback()
    def on_location_selected(self, widget, data):
        """capture the Notify for the selected property is changed"""
        location = FlatpakLocation(self.location.get_selected_item().get_string())
        remotes = self.backend.get_remotes(location=location)
        if remotes:
            model = Gtk.StringList.new()
            for remote in remotes:
                model.append(remote)
            self.remote.set_model(model)
        else:
            self._clear()

    def _set_icon(self, id: str, remote_name: str):
        if not remote_name:
            self.icon.set_from_icon_name("flatpak-symbolic")
            return
        icon_path = self.backend.get_icon_path(remote_name)
        icon_file = Path(f"{icon_path}/{id}.png")
        if icon_file.exists():
            self.icon.set_from_file(icon_file.as_posix())
        else:
            self.icon.set_from_icon_name("flatpak-symbolic")

    def _set_selected_num(self):
        """update the current selected number"""
        self.found_num.set_visible(True)
        num = len(self.found_ids)
        label = f"{self.found_ndx+1}/{num}"
        self.found_num.set_label(label)

    def _clear(self) -> None:
        self.found_ids = []
        self.found_ndx = 0
        self.current_id.set_title("")
        self._set_icon("", None)  # reset icon
        self.found_num.set_visible(False)

    @Gtk.Template.Callback()
    def on_search(self, widget):
        key = widget.get_text()
        selected = self.remote.get_selected_item()
        if key == "" or not selected or len(key) < 3:
            self._clear()
            return
        remote_name = selected.get_string()
        location = FlatpakLocation(self.location.get_selected_item().get_string())
        self.found_ids = self.backend.find(remote_name, key, location=location)
        log(f"found : {len(self.found_ids)}")
        self.found_ndx = 0
        if self.found_ids:
            fp_id = self.found_ids[self.found_ndx]
            self._set_icon(fp_id, remote_name)
            self.current_id.set_title(fp_id)
            self._set_selected_num()
        else:
            self._clear()

    @Gtk.Template.Callback()
    def on_search_next_match(self, widget) -> None:
        log("search next match")
        if self.found_ndx < len(self.found_ids) - 1:
            self.found_ndx += 1
            fp_id = self.found_ids[self.found_ndx]
            remote_name = self.remote.get_selected_item().get_string()
            self._set_icon(fp_id, remote_name)
            self.current_id.set_title(fp_id)
            self._set_selected_num()

    @Gtk.Template.Callback()
    def on_search_previous_match(self, widget) -> None:
        log("search next match")
        if self.found_ndx > 0:
            self.found_ndx -= 1
            fp_id = self.found_ids[self.found_ndx]
            remote_name = self.remote.get_selected_item().get_string()
            self._set_icon(fp_id, remote_name)
            self.current_id.set_title(fp_id)
            self._set_selected_num()
