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


@Gtk.Template(resource_path=f"{rootdir}/ui/progress.ui")
class YumexProgress(Adw.Window):
    __gtype_name__ = "YumexProgress"

    title = Gtk.Template.Child()
    subtitle = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win = win

    def show(self):
        self.present()

    def hide(self):
        self.close()

    def set_title(self, title: str):
        self.title.set_label(title)

    def set_subtitle(self, title: str):
        self.subtitle.set_label(title)
