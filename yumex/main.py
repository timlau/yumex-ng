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
# Copyright (C) 2023  Tim Lauridsen
#
#


import sys
import argparse
import subprocess
import logging
from traceback import format_exception

from gi.repository import Gtk, Gio, Adw

from yumex.ui.window import YumexMainWindow
from yumex.ui.preferences import YumexPreferences
from yumex.utils import setup_logging, log
from yumex.constants import rootdir, app_id, version, backend, build_type
from yumex.ui.dialogs import error_dialog
from typing import Literal


class YumexApplication(Adw.Application):
    """The main application singleton class."""

    __gtype_name__ = "YumexApplication"
    settings = Gio.Settings.new(app_id)

    def __init__(self) -> None:
        super().__init__(
            application_id=app_id, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        )
        self.set_resource_base_path(rootdir)
        self.style_manager = Adw.StyleManager.get_default()
        self.args = None

    def do_activate(self) -> None:
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """

        self.win: YumexMainWindow = self.props.active_window
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
        self.create_action("preferences", self.on_preferences, ["<Ctrl>comma"])

        # windows related actions
        self.create_action("select_all", self.win.on_actions, ["<Ctrl>A"])
        self.create_action("deselect_all", self.win.on_actions, ["<Shift><Ctrl>A"])
        self.create_action("sidebar", self.win.on_actions, ["F9"])
        self.create_action("clear_queue", self.win.on_actions)
        self.create_action("filter_installed", self.win.on_actions, ["<Alt>I"])
        self.create_action("filter_updates", self.win.on_actions, ["<Alt>U"])
        self.create_action("filter_available", self.win.on_actions, ["<Alt>A"])
        self.create_action("toggle_selection", self.win.on_actions, ["<Ctrl>space"])
        self.create_action("filter_search", None)
        self.create_action("flatpak_update", self.win.on_actions)
        self.create_action("flatpak_install", self.win.on_actions, ["<Ctrl>I"])
        self.create_action("flatpak_remove", self.win.on_actions, ["<Ctrl>X"])
        self.create_action("apply_actions", self.win.on_actions, ["<Ctrl>Return"])
        self.create_action("page_one", self.win.on_actions, ["<Alt>1"])
        self.create_action("page_two", self.win.on_actions, ["<Alt>2"])
        self.create_action("page_three", self.win.on_actions, ["<Alt>3"])

        # call a test function to test gui code, should not be enabled, if not testing
        if build_type == "debug" or self.args.debug:
            self.create_action("testing", self.win.on_testing, ["<Shift><Ctrl>T"])

        self.win.present()
        # click the Availble package filter, without looking the UI
        self.win.load_packages("installed")

    def do_command_line(self, args) -> Literal[0]:
        parser = argparse.ArgumentParser(
            prog="yumex", description="Yum Extender package managemnt application"
        )
        parser.add_argument(
            "-d", "--debug", help="enable debug logging", action="store_true"
        )
        parser.add_argument(
            "--exit", help="stop the dnfdaemon system daemon", action="store_true"
        )
        self.args = parser.parse_args(args.get_arguments()[1:])
        if self.args.exit:
            subprocess.call(
                "/usr/bin/dbus-send --system --print-reply "
                "--dest=org.baseurl.DnfSystem / org.baseurl.DnfSystem.Exit",
                shell=True,
            )
            return 0
        setup_logging(debug=self.args.debug)
        log(f" commmand-line : {self.args}")
        self.activate()
        return 0

    def create_action(self, name, callback, shortcuts=None) -> None:
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
            activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        if callback:
            action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def on_about(self, *_args) -> None:
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="Yum Extender",
            application_icon=app_id,
            developer_name="Tim Lauridsen",
            website="https://yumex.dk",
            support_url="",
            issue_url="https://github.com/timlau/yumex-ng/issues",
            developers=["Tim Lauridsen"],
            artists=[],
            designers=[],
            documenters=[],
            translator_credits="",
            copyright="?? 2023 Tim Lauridsen",
            license_type=Gtk.License.GPL_3_0,
            version=f"{version} ({backend})",
            release_notes_version=version,
            release_notes=_(
                """
<ul>
<li>Browse installed flatpaks</li>
<li>Install, remove and update flatpaks</li>
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

    def on_preferences(self, *_args) -> None:
        prefs = YumexPreferences(self.win)
        prefs.set_transient_for(self.win)
        prefs.present()

    def exception_hook(self, exc_type, exc_value, exc_traceback) -> None:
        logging.critical(
            f"Uncaught exception: {exc_value}",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        msg = "".join(format_exception(exc_type, exc_value, exc_traceback, None))
        error_dialog(self.win, title="Uncaught exception", msg=msg)


def main() -> int:
    """The application's entry point."""
    app = YumexApplication()
    sys.excepthook = app.exception_hook
    return app.run(sys.argv)
