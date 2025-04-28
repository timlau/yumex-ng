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

from gi.repository import Adw, GObject, Gtk

from yumex.constants import ROOTDIR

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/advanced_actions.ui")
class YumexAdvancedActions(Adw.Dialog):
    __gtype_name__ = "YumexAdvancedActions"
    # __gsignals__ = {"action": (GObject.SignalFlags.RUN_FIRST, None, ())}

    """Advanced actions dialog."""
    releasever = Gtk.Template.Child()
    cancel_upgrade = Gtk.Template.Child()
    system_upgrade = Gtk.Template.Child()
    offline = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win = win
        self.presenter = win.presenter

    def show(self, win):
        """Show the dialog."""
        self.present(win)
        # Set button sensitivity based on if there is an offline transaction
        # has_transaction = False
        has_transaction = self.presenter.has_offline_transaction()
        if has_transaction:
            self.offline.set_visible(True)
            self.system_upgrade.set_visible(False)
        else:
            self.offline.set_visible(False)
            self.system_upgrade.set_visible(True)

    @GObject.Signal(flags=GObject.SignalFlags.RUN_LAST, arg_types=(str, str))
    def action(self, action, parameter):
        """Signal emitted when an action is performed."""
        pass

    @Gtk.Template.Callback()
    def on_refresh_dnf_cache(self, button):
        """Refresh the DNF cache."""
        self.close()
        self.emit("action", "refresh-cache", None)

    @Gtk.Template.Callback()
    def on_distro_sync_system(self, button):
        """Distro sync on all installed packages"""
        self.close()
        self.emit("action", "distro-sync-system", None)

    @Gtk.Template.Callback()
    def on_system_upgrade(self, button):
        """Perform a system upgrade"""
        self.close()
        releasever = self.releasever.get_text()
        self.emit("action", "system-upgrade", releasever)

    @Gtk.Template.Callback()
    def on_cancel_system_upgrade(self, button):
        """Perform a system upgrade"""
        self.close()
        releasever = self.releasever.get_text()
        self.emit("action", "cancel-system-upgrade", releasever)

    @Gtk.Template.Callback()
    def on_reboot(self, button):
        """Perform a system upgrade"""
        self.close()
        self.emit("action", "reboot", "")
