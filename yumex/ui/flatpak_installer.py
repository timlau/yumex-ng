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

from pathlib import Path
from gi.repository import Gtk, Adw
from yumex.backend.flatpak.backend import FlatpakBackend

from yumex.constants import rootdir
from yumex.utils import log


@Gtk.Template(resource_path=f"{rootdir}/ui/flatpak_installer.ui")
class YumexFlatpakInstaller(Adw.Window):
    __gtype_name__ = "YumexFlatpakInstaller"

    search_id: Gtk.SearchEntry = Gtk.Template.Child()
    current_id: Adw.ActionRow = Gtk.Template.Child()
    remote: Adw.ComboRow = Gtk.Template.Child()
    location: Adw.ComboRow = Gtk.Template.Child()
    icon: Gtk.Image = Gtk.Template.Child()
    found_num: Gtk.Label = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win: YumexMainWindow = win
        self.confirm = False
        self.found_ids: list[str] = []
        self.found_ndx: int = 0
        self.setup_location()
        self.read_clipboard()
        self.search_id.set_key_capture_widget(self)
        self.search_id.grab_focus()
        self.icon.set_from_icon_name("flatpak-symbolic")

    def setup_location(self):
        fp_location = self.win.settings.get_string("fp-location")
        ndx = 0
        for location in self.location.get_model():
            if location.get_string() == fp_location:
                self.location.set_selected(ndx)
            ndx += 1

    def read_clipboard(self):
        """If the the clipboard contains

        flatpak install flathub <some id>

        then use these values
        """

        def callback(obj, res, *args):
            text = clb.read_text_finish(res)
            if text and text.startswith("flatpak install"):
                words = text.split(" ")
                self.search_id.set_text(words[3])
                ndx = 0
                for remote in self.remote.get_model():
                    if remote.get_string() == words[2]:
                        self.remote.set_selected(ndx)
                    ndx += 1
            else:
                fp_source = self.win.settings.get_string("fp-source")
                ndx = 0
                for remote in self.remote.get_model():
                    if remote.get_string() == fp_source:
                        self.remote.set_selected(ndx)
                    ndx += 1

        clb = self.win.get_clipboard()
        clb.read_text_async(None, callback)

    @property
    def backend(self) -> FlatpakBackend:
        return self.win.flatpak_view.backend

    @Gtk.Template.Callback()
    def on_ok_clicked(self, *args):
        log("flafpak_installer Ok clicked")
        self.confirm = True
        self.close()

    @Gtk.Template.Callback()
    def on_cancel_clicked(self, *args):
        log("flafpak_installer cancel clicked")
        self.close()

    @Gtk.Template.Callback()
    def on_location_notify(self, widget, data):
        """capture the Notify for the selected property is changed"""
        match data.name:
            case "selected":
                location = self.location.get_selected_item()
                remotes = Gtk.StringList.new()
                for remote in self.backend.get_remotes(location=location.get_string()):
                    remotes.append(remote)
                self.remote.set_model(remotes)

    def _set_icon(self, id: str, remote_name: str):
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

    @Gtk.Template.Callback()
    def on_search(self, widget):
        key = widget.get_text()
        remote_name = self.remote.get_selected_item().get_string()
        if key == "":
            self.found_ids = []
            self.found_ndx = 0
            self.current_id.set_title("")
            self._set_icon("", remote_name)  # reset icon
            self.found_num.set_visible(False)
            return
        if len(key) < 3:
            return
        self.found_ids = self.backend.find(remote_name, key)
        log(f"found : {len(self.found_ids)}")
        self.found_ndx = 0
        if self.found_ids:
            id = self.found_ids[self.found_ndx]
            self._set_icon(id, remote_name)
            self.current_id.set_title(id)
            self._set_selected_num()
        else:
            self.current_id.set_title("")
            self._set_icon("", remote_name)  # reset icon
            self.found_num.set_visible(False)

    @Gtk.Template.Callback()
    def on_search_next_match(self, widget) -> None:
        log("search next match")
        if self.found_ndx < len(self.found_ids) - 1:
            self.found_ndx += 1
            id = self.found_ids[self.found_ndx]
            remote_name = self.remote.get_selected_item().get_string()
            self._set_icon(id, remote_name)
            self.current_id.set_title(id)
            self._set_selected_num()

    @Gtk.Template.Callback()
    def on_search_previous_match(self, widget) -> None:
        log("search next match")
        if self.found_ndx > 0:
            self.found_ndx -= 1
            id = self.found_ids[self.found_ndx]
            remote_name = self.remote.get_selected_item().get_string()
            self._set_icon(id, remote_name)
            self.current_id.set_title(id)
            self._set_selected_num()
