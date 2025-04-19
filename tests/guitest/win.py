import logging

from gi.repository import Adw, Gtk  # type: ignore

logger = logging.getLogger(__name__)

from test import run_test


class GuiTestWindow(Adw.ApplicationWindow):
    """Main application window."""

    def __init__(self, application):
        super().__init__(application=application)
        self.set_default_size(1000, 1000)
        self.set_title("Testing GUI")
        main_content = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)
        left_button = Gtk.Button(label="Run Test")
        left_button.connect("clicked", self.on_run_test)
        header.pack_start(left_button)
        main_content.add_top_bar(header)
        self.set_content(main_content)

    def on_run_test(self, widget):
        run_test(self)
