
import sys

from gi.repository import Gtk, Gdk, Gio, Adw, GLib

from yumex.ui.window import YumexMainWindow
from yumex.constants import (
    rootdir,
    app_id,
    rel_ver,
    version,
)

class YumexApplication(Adw.Application):
    """The main application singleton class."""

    __gtype_name__ = "YumexApplication"

    def __init__(self):
        super().__init__(application_id=app_id, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.set_resource_base_path(rootdir)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """

        self.win = self.props.active_window
        if not self.win:
            self.win = YumexMainWindow(
                application=self,
            )
        self.win.present()

def main():
    """The application's entry point."""
    print('yumex is running')
    app = YumexApplication()
    return app.run(sys.argv)
