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
        self.style_manager = Adw.StyleManager.get_default()


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

        # self.create_action("apply_actions", self.on_apply_actions)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource(f"{rootdir}/style.css")
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)        
        self.create_action("about", self.on_about)
        self.create_action("preferences", self.on_preferences)
        print(f"dark mode: {self.style_manager.get_dark()}")
        self.win.present()

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

    def on_about(self, widget, data):
        self.win.show_message("About pressed")

    def on_preferences(self, widget, data):
        self.win.show_message("Preferences pressed")

def main():
    """The application's entry point."""
    print("yumex is running")
    app = YumexApplication()
    return app.run(sys.argv)
