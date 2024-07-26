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
# Copyright (C) 2024 Tim Lauridsen
#
#


from pathlib import Path
import sys
import argparse
import subprocess
from traceback import format_exception

from gi.repository import Gtk, Gio, Adw  # type: ignore

from yumex.ui.window import YumexMainWindow
from yumex.ui.preferences import YumexPreferences
from yumex.utils import setup_logging, log, logger
from yumex.constants import ROOTDIR, APP_ID, VERSION, BACKEND, BUILD_TYPE
from yumex.ui.dialogs import error_dialog
from typing import Literal


class YumexApplication(Adw.Application):
    """The main application singleton class."""

    __gtype_name__ = "YumexApplication"
    settings = Gio.Settings.new(APP_ID)

    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.set_resource_base_path(ROOTDIR)
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
            window_height = self.settings.get_int("window-height")
            window_width = self.settings.get_int("window-width")
            fullscreened = self.settings.get_boolean("window-fullscreen")
            maximized = self.settings.get_boolean("window-maximized")
            log(f"window-height: {window_height}")
            log(f"window-width: {window_width}")
            log(f"fullscreened: {fullscreened}")
            log(f"maximized: {maximized}")

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
        self.create_action("flatpak_search", self.win.on_actions, ["<Ctrl>S"])
        self.create_action("flatpak_remove", self.win.on_actions, ["Delete"])
        self.create_action("flatpak_runtime", self.win.on_actions)
        self.create_action("flatpak_remove_unused", self.win.on_actions)

        self.create_action("apply_actions", self.win.on_actions, ["<Ctrl>Return"])
        self.create_action("page_one", self.win.on_actions, ["<Alt>1"])
        self.create_action("page_two", self.win.on_actions, ["<Alt>2"])
        self.create_action("page_three", self.win.on_actions, ["<Alt>3"])

        # call a test function to test gui code, should not be enabled, if not testing
        if BUILD_TYPE == "debug" or self.args.debug:
            self.create_action("testing", self.win.on_testing, ["<Shift><Ctrl>T"])

        self.win.present()
        # click the Availble package filter, without looking the UI
        if self.args.flatpakref:
            self.win.install_flatpakref(self.args.flatpakref)
        elif self.args.update:
            self.win.load_packages("updates")
        else:
            self.win.load_packages("installed")

    def do_command_line(self, args) -> Literal[0]:
        parser = argparse.ArgumentParser(prog="yumex", description="Yum Extender package management application")
        parser.add_argument("-d", "--debug", help="enable debug logging", action="store_true")
        parser.add_argument("--exit", help="stop the dnfdaemon system daemon", action="store_true")
        parser.add_argument("--update", help="start on update page", action="store_true")
        parser.add_argument("--flatpakref", help="Install flatpak from a .flatpakref")
        self.args = parser.parse_args(args.get_arguments()[1:])
        if self.args.exit:
            subprocess.call(
                "/usr/bin/dbus-send --system --print-reply "
                "--dest=org.baseurl.DnfSystem / org.baseurl.DnfSystem.Exit",
                shell=True,
            )
            return 0
        setup_logging(debug=self.args.debug)
        global is_local
        log(f"Version:  {VERSION} ({BACKEND})")
        log(f"executable : {args.get_arguments()[0]}")
        log(f"commmand-line : {self.args}")
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
        # FIXME: libadwaita 1.5 uses Adw.AboutDialog, Adw.AboutWindow will be deprecated in 1.6
        #  about = Adw.AboutDialog(
        about = Adw.AboutWindow(
            application_name="Yum Extender",
            application_icon=APP_ID,
            developer_name="Tim Lauridsen",
            website="https://yumex.dk",
            support_url="",
            issue_url="https://github.com/timlau/yumex-ng/issues",
            developers=["Tim Lauridsen", "Thomas Crider (GloriousEggroll)"],
            artists=[],
            designers=[],
            documenters=[],
            translator_credits="",
            copyright="© 2024 Tim Lauridsen",
            license_type=Gtk.License.GPL_3_0,
            version=f"{VERSION} ({BACKEND})",
            release_notes_version=VERSION,
            release_notes=_(
                """
        <ul>
          <li>Added background update checker</li>
          <li>Sending Notifications on available updates</li>
          <li>Show system tray icon on supported systems (gnome need appindicator extension)</li>
          <li>lot of code fixes and optimization</li>
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
        about.add_acknowledgement_section(
            _("Special thanks to"),
            ["Thomas Crider https://github.com/GloriousEggroll"],
        )

        # about.set_presentation_mode(Adw.DialogPresentationMode.ADW_DIALOG_FLOATING)

        # FIXME: for libadwaita 1.5 (Adw.AboutDialog) about.present(self.win)
        about.present()
        about.set_transient_for(self.win)  # FIXME: not needed for libadwaita 1.5

    def on_preferences(self, *_args) -> None:
        prefs = YumexPreferences(self.win.presenter)
        prefs.set_transient_for(self.win)
        prefs.present()

    def exception_hook(self, exc_type, exc_value, exc_traceback) -> None:
        logger.critical(
            f"Uncaught exception: {exc_value}",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        msg = "".join(format_exception(exc_type, exc_value, exc_traceback, None))

        # create timestamp
        from datetime import datetime

        current_datetime = datetime.now()
        timestamp = current_datetime.strftime("%m-%d-%Y_%H%M%S")

        tb_file = Path(f"~/.local/share/yumex/traceback_{timestamp}.txt").expanduser()
        tb_file.parent.mkdir(exist_ok=True)
        tb_file.write_text(msg)
        log(f"traceback written to {tb_file}")
        error_dialog(self.win, title="Uncaught exception", msg=msg)


def main() -> int:
    """The application's entry point."""
    app = YumexApplication()
    sys.excepthook = app.exception_hook
    return app.run(sys.argv)
