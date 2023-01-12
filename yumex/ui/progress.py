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

from gi.repository import Gtk, Adw

from yumex.constants import rootdir


@Gtk.Template(resource_path=f"{rootdir}/ui/progress.ui")
class YumexProgress(Adw.Window):
    __gtype_name__ = "YumexProgress"

    title = Gtk.Template.Child()
    subtitle = Gtk.Template.Child()
    progress = Gtk.Template.Child()
    ok_button = Gtk.Template.Child()
    spinner = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win: YumexMainWindow = win

    def show(self):
        self.set_transient_for(self.win)
        self.spinner.set_visible(True)
        self.present()

    def hide(self):
        self.close()
        self.set_title("")
        self.set_subtitle("")

    def set_title(self, title: str):
        self.title.set_label(title)
        self.set_subtitle("")
        self.set_progress(0.0)
        self.progress.set_visible(False)

    def set_subtitle(self, title: str):
        self.subtitle.set_label(title)

    def show_button(self):
        self.spinner.set_visible(False)
        self.ok_button.set_visible(True)

    def set_progress(self, frac: float):
        if frac >= 0.0 and frac <= 1.0:
            self.progress.set_visible(True)
            self.progress.set_fraction(frac)

    @Gtk.Template.Callback()
    def on_ok_clicked(self, *args):
        self.ok_button.set_visible(False)
        self.hide()
