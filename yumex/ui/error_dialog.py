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

import html
import logging

from gi.repository import Adw, GLib, Gtk

from yumex.constants import ROOTDIR

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/error_dialog.ui")
class YumexErrorDialog(Adw.Dialog):
    __gtype_name__ = "YumexErrorDialog"

    title_row: Adw.ActionRow = Gtk.Template.Child()
    errors: Gtk.Label = Gtk.Template.Child()
    quit_button = Gtk.Template.Child("quit")
    copy_button = Gtk.Template.Child("copy")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._loop = GLib.MainLoop()

    def show_dialog(self, win):
        self.present(win)
        self._loop.run()

    def set_error(self, errors) -> None:
        errors = str(errors)
        errors = html.escape(errors)
        self.set_follows_content_size(True)
        self.errors.set_text(errors)

    def set_title(self, title: str):
        self.title_row.set_title(title)

    @Gtk.Template.Callback()
    def on_quit_clicked(self, button):
        self._loop.quit()
        self.confirm = True
        self.close()

    @Gtk.Template.Callback()
    def on_copy_clicked(self, button):
        """Copy the errors to the clipboard."""
        subtitle = self.errors.get_text()
        clb = button.get_clipboard()
        clb.set(subtitle)
