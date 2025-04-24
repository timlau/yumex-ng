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

from gi.repository import Adw, Gtk

from yumex.constants import ROOTDIR


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/progress.ui")
class YumexProgress(Adw.Dialog):
    __gtype_name__ = "YumexProgress"

    title: Gtk.Label = Gtk.Template.Child()
    subtitle: Gtk.Label = Gtk.Template.Child()
    progress: Gtk.ProgressBar = Gtk.Template.Child()
    spinner: Gtk.Spinner = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self._is_shown = False
        self.win = win

    def show(self):
        # self.spinner.set_visible(True)
        self._is_shown = True
        self.present(self.win)

    def hide(self, clear: bool = True):
        if self._is_shown:
            self._is_shown = False
            self.close()
            if clear:
                self.set_title("")
                self.set_subtitle("")

    def set_title(self, title: str):
        self.title.set_label(title)
        self.set_subtitle("")
        self.set_progress(0.0)
        self.progress.set_visible(False)

    def set_subtitle(self, title: str):
        self.subtitle.set_label(title)

    def set_progress(self, frac: float):
        if frac >= 0.0 and frac <= 1.0:
            self.progress.set_visible(True)
            self.progress.set_fraction(frac)
