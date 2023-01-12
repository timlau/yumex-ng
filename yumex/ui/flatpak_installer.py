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

    id: Adw.EntryRow = Gtk.Template.Child()
    source: Adw.ComboRow = Gtk.Template.Child()
    location: Adw.ComboRow = Gtk.Template.Child()
    icon: Gtk.Image = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win: YumexMainWindow = win
        self.confirm = False
        self.setup_location()
        self.read_clipboard()
        self.id.grab_focus()
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
                self.id.set_text(words[3])
                ndx = 0
                for source in self.source.get_model():
                    if source.get_string() == words[2]:
                        self.source.set_selected(ndx)
                    ndx += 1
            else:
                fp_source = self.win.settings.get_string("fp-source")
                ndx = 0
                for source in self.source.get_model():
                    if source.get_string() == fp_source:
                        self.source.set_selected(ndx)
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
                self.source.set_model(remotes)

    def _set_icon(self, id: str, remote_name: str):
        icon_path = self.backend.get_icon_path(remote_name)
        icon_file = Path(f"{icon_path}/{id}.png")
        if icon_file.exists():
            self.icon.set_from_file(icon_file.as_posix())
        else:
            self.icon.set_from_icon_name("flatpak-symbolic")

    @Gtk.Template.Callback()
    def on_apply(self, widget):
        key = widget.get_text()
        remote_name = self.source.get_selected_item().get_string()
        id = self.backend.find(remote_name, key)
        if id:
            widget.set_text(id)
            self._set_icon(id, remote_name)

        else:
            widget.set_text("")
            self._set_icon("", remote_name)  # reset icon
