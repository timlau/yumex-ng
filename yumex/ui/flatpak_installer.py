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

from gi.repository import Gtk, Adw  # noqa: F401

from yumex.constants import rootdir  # noqa: F401
from yumex.utils import log  # noqa: F401


@Gtk.Template(resource_path=f"{rootdir}/ui/flatpak_installer.ui")
class YumexFlatpakInstaller(Adw.Window):
    __gtype_name__ = "YumexFlatpakInstaller"

    id = Gtk.Template.Child()
    source = Gtk.Template.Child()
    location = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win = win
        self.confirm = False

    @property
    def backend(self):
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
                match location.get_string():
                    case "user":
                        system = False
                    case "system":
                        system = True
                remotes = Gtk.StringList.new()
                for remote in self.backend.get_remotes(system=system):
                    remotes.append(remote)
                self.source.set_model(remotes)

    @Gtk.Template.Callback()
    def on_apply(self, widget):
        key = widget.get_text()
        remote = self.source.get_selected_item().get_string()
        id = self.backend.find(remote, key)
        if id:
            widget.set_text(id)
        else:
            widget.set_text("")
