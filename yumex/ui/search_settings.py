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
# Copyright (C) 2025 Tim Lauridsen

import logging

from gi.repository import Adw, GLib, Gtk

from yumex.constants import ROOTDIR

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/search_settings.ui")
class YumexSearchSettings(Adw.PreferencesDialog):
    __gtype_name__ = "YumexSearchSettings"

    with_filenames = Gtk.Template.Child()
    with_provides = Gtk.Template.Child()
    with_binaries = Gtk.Template.Child()
    arch = Gtk.Template.Child()
    scope = Gtk.Template.Child()
    latest_limit: Adw.SpinRow = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("unrealize", self.on_close)
        self.options = {}
        self._loop = GLib.MainLoop()
        self.latest_limit.set_value(1.0)

    def show(self, win):
        self.present(win)
        self._loop.run()
        return self.options

    def get_dnf_options(self):
        """Get the dnf options from the search settings dialog."""
        #     options["repo"] = kwargs.pop("repo")

        options = {
            "with_filenames": self.with_filenames.get_active(),
            "with_provides": self.with_provides.get_active(),
            "with_binaries": self.with_binaries.get_active(),
            "scope": self.scope.get_selected_item().get_string(),
            "latest_limit": int(self.latest_limit.get_value()),
        }
        arch = self.arch.get_selected_item().get_string()
        if arch != "all":
            options["arch"] = [arch]

        return options

    def on_close(self, *args):
        """Close the search settings dialog."""
        self._loop.quit()
        self.options = self.get_dnf_options()
        self.close()
