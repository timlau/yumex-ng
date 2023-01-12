from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yumex.ui.window import YumexMainWindow

import sys

from gi.repository import Adw


def error_dialog(win: YumexMainWindow, title: str, msg: str):
    def response(dialog, result, *args):
        sys.exit(1)

    dialog = Adw.MessageDialog.new(
        win,
        title,
        msg,
    )
    dialog.add_response("quit", _("Quit"))
    dialog.set_default_response("quit")
    dialog.set_close_response("quit")
    dialog.connect("response", response)
    dialog.present()
