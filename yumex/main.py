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
#
# Copyright (C) 2022  Tim Lauridsen
#
#


import sys
import argparse

from gi.repository import Gtk, Gdk, Gio, Adw, GLib  # noqa: F401

from yumex.ui.window import YumexMainWindow
from yumex.ui.preferences import YumexPreferences
from yumex.utils import setup_logging, log
from yumex.constants import (  # noqa: F401
    rootdir,
    app_id,
    rel_ver,
    version,
)


class YumexApplication(Adw.Application):
    """The main application singleton class."""

    __gtype_name__ = "YumexApplication"
    settings = Gio.Settings.new(app_id)

    def __init__(self):
        super().__init__(
            application_id=app_id, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        )
        self.set_resource_base_path(rootdir)
        self.style_manager = Adw.StyleManager.get_default()
        self.args = None

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """

        self.win = self.props.active_window
        if not self.win:
            self.win = YumexMainWindow(
                application=self,
                default_height=self.settings.get_int("window-height"),
                default_width=self.settings.get_int("window-width"),
                fullscreened=self.settings.get_boolean("window-fullscreen"),
                maximized=self.settings.get_boolean("window-maximized"),
            )

        # create app actions
        self.create_action("about", self.on_about)
        self.create_action("preferences", self.on_preferences)
        self.create_action("select_all", self.win.on_selectall_activate)
        self.create_action("deselect_all", self.win.on_deselectall_activate)
        log(f"dark mode: {self.style_manager.get_dark()}")
        self.win.present()
        # click the Availble package filter, without looking the UI
        self.win.load_packages("installed")

    def do_command_line(self, args):
        parser = argparse.ArgumentParser(prog="app")
        parser.add_argument("-d", "--debug", action="store_true")
        self.args = parser.parse_args(args.get_arguments()[1:])
        setup_logging(debug=self.args.debug)
        log(f" commmand-line : {self.args}")
        self.activate()
        return 0

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
            activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def on_about(self, *_args):
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="Yum Extender",
            application_icon=app_id,
            developer_name="Tim Lauridsen",
            website="https://yumex.dk",
            support_url="",
            issue_url="https://github.com/timlau/yumex-ng",
            developers=["Tim Lauridsen"],
            artists=[],
            designers=[],
            documenters=[],
            translator_credits="",
            copyright="© 2022 Tim Lauridsen",
            license_type=Gtk.License.GPL_3_0,
            version=version,
            release_notes_version=version,
            release_notes=_(
                """
<ul>
<li>Early Build, not released yet</li>
</ul>
"""
            ),
            comments=_(
                """
Yum Extender is a Package management to install, update and remove packages
"""
            ),
        )
        # about.add_credit_section(
        #     _("Section title"),
        #     ["Somebody https://yumex.dk"],
        # )
        # about.add_acknowledgement_section(
        #     _("Special thanks to"),
        #     ["Somebody https://yumex.dk"],
        # )

        about.present()

    def on_preferences(self, *_args):
        prefs = YumexPreferences(self.win)
        prefs.set_transient_for(self.win)
        prefs.present()


def main():
    """The application's entry point."""
    app = YumexApplication()
    return app.run(sys.argv)
