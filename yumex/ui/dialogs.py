from gi.repository import Adw, GLib

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


class GPGDialog(Adw.MessageDialog):
    def __init__(self, win: MainWindow, key_values: tuple):
        super().__init__()
        (
            pkg_id,
            userid,
            hexkeyid,
            keyurl,
            timestamp,
        ) = key_values
        self.set_heading(_("Install GPG Key"))
        body = f"""
        {userid}

        {pkg_id}
        """
        self.set_body(body)
        self.install_key = False
        self._loop = GLib.MainLoop()
        self.add_response("yes", _("Yes"))
        self.set_response_appearance("yes", Adw.ResponseAppearance.DESTRUCTIVE)
        self.add_response("no", _("No"))
        self.set_default_response("no")
        self.set_close_response("no")
        self.connect("response", self.response)

    def response(self, dialog, result, *args):
        self.install_key = result == "yes"
        self._loop.quit()
        self.close()

    def show(self):
        self.present()
        self._loop.run()
