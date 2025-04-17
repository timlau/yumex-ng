import logging

from gi.repository import Adw, Gio  # type: ignore
from win import GuiTestWindow

from yumex.constants import APP_ID, ROOTDIR

logger = logging.getLogger(__name__)


class GuiTestApplication(Adw.Application):
    """The main application singleton class."""

    __gtype_name__ = "GuiTestApplication"
    settings = Gio.Settings.new(APP_ID)

    def __init__(self) -> None:
        super().__init__(application_id=APP_ID)
        self.set_resource_base_path(ROOTDIR)
        self.style_manager = Adw.StyleManager.get_default()

    def do_activate(self) -> None:
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """

        self.win = self.props.active_window
        if not self.win:
            self.win = GuiTestWindow(application=self)
        self.win.present()
