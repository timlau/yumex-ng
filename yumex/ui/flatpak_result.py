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

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from yumex.constants import ROOTDIR
from yumex.utils.enums import FlatpakAction, FlatpakLocation

logger = logging.getLogger(__name__)


class ResultElem(GObject.GObject):
    def __init__(self, ref: str, action: FlatpakAction, source: str, location: FlatpakLocation) -> None:
        super().__init__()
        self.ref: str = ref
        self.action: FlatpakAction = action
        self.source: str = source
        self.location: FlatpakLocation = location

    def __str__(self) -> str:
        match self.action:
            case FlatpakAction.INSTALL:
                action_str = _("Installing")
            case FlatpakAction.UNINSTALL:
                action_str = _("Uninstalling")
            case _:
                action_str = _("Updating")
        return f"{action_str} : <i>{self.location.upper()}</i>  - <b>{self.ref}</b> <small>({self.source})</small> "  # noqa


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/flatpak_result.ui")
class YumexFlatpakResult(Adw.Window):
    __gtype_name__ = "YumexFlatpakResult"

    result_view = Gtk.Template.Child()
    selection = Gtk.Template.Child()
    result_factory = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.confirm = False
        self._loop = GLib.MainLoop()
        self.store = Gio.ListStore.new(ResultElem)
        self.selection.set_model(self.store)

    def show(self):
        self.present()
        self._loop.run()

    def populate(self, results: list[str, FlatpakAction, str]):
        for ref, action, source, location in results:
            elem = ResultElem(ref, action, source, location)
            logger.debug(f" --> Adding element {elem}")
            self.store.append(elem)
        self.store.sort(lambda a, b: a.location + a.ref > b.location + b.ref)

    @Gtk.Template.Callback()
    def on_confirm_clicked(self, button):
        self._loop.quit()
        self.confirm = True
        self.close()

    @Gtk.Template.Callback()
    def on_cancel_clicked(self, button):
        self._loop.quit()
        self.close()

    @Gtk.Template.Callback()
    def on_setup(self, widget, item):
        """Setup the widget to show in the Gtk.Listview"""
        label = Gtk.Label()
        label.set_xalign(0.0)
        item.set_child(label)

    @Gtk.Template.Callback()
    def on_bind(self, widget, item):
        """bind data from the store object to the widget"""
        label = item.get_child()
        obj: ResultElem = item.get_item()
        label.set_markup(str(obj))
