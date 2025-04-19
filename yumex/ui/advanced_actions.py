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
import re
from ast import Gt
from platform import release

from gi.repository import Adw, GObject, Gtk

from yumex.constants import ROOTDIR

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/advanced_actions.ui")
class YumexAdvancedActions(Adw.Dialog):
    __gtype_name__ = "YumexAdvancedActions"
    # __gsignals__ = {"action": (GObject.SignalFlags.RUN_FIRST, None, ())}

    """Advanced actions dialog."""
    releasever = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win = win
        self.action = None

    def show(self, win):
        """Show the dialog."""
        self.action = None
        self.present(win)
        return self.action

    @GObject.Signal(flags=GObject.SignalFlags.RUN_LAST, arg_types=(str, str))
    def action(self, action, parameter):
        """Signal emitted when an action is performed."""
        pass

    @Gtk.Template.Callback()
    def on_refresh_dnf_cache(self, button):
        """Refresh the DNF cache."""
        self.action = "refresh-cache"
        self.close()
        self.emit("action", "refresh-cache", None)

    @Gtk.Template.Callback()
    def on_distro_sync(self, button):
        """Perform a distribution sync."""
        self.action = "distro-sync"
        self.close()
        releasever = self.releasever.get_text()
        self.emit("action", "distro-sync", releasever)
