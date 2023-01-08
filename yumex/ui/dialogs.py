import sys

from gi.repository import Adw, GLib


def error_dialog(win: Adw.ApplicationWindow, title: str, msg: str):
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


class ResultDialog:
    def __init__(self, win: Adw.ApplicationWindow, title: str, msg: str):
        self.result = None
        self._loop = GLib.MainLoop()
        header = "The following flatpaks will be affected:\n\n"
        footer = "\n\n"
        dialog = Adw.MessageDialog.new(
            win,
            title,
            header + msg + footer,
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("confirm", _("Confirm"))
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.response)
        dialog.present()
        self._loop.run()

    def response(self, dialog, result, *args):
        self._loop.quit()
        self.result = result
