from gi.repository import Adw

from yumex.utils.types import MainWindow


def error_dialog(win: MainWindow, title: str, msg: str):
    def response(dialog, result, *args):
        raise SystemExit

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
