from gi.repository import Adw, GLib

from yumex.utils.types import MainWindow


def error_dialog(win: MainWindow, title: str, msg: str):
    def response(dialog, result, *args):
        raise SystemExit

    dialog = Adw.AlertDialog.new(
        title,
        msg,
    )
    dialog.set_content_width(600)
    dialog.set_content_height(500)
    dialog.set_follows_content_size(False)
    dialog.add_response("quit", _("Quit"))
    dialog.set_default_response("quit")
    dialog.set_close_response("quit")
    dialog.connect("response", response)
    dialog.add_css_class("error_dialog")
    dialog.present(win)


# TODO: Make a custom GPG Dialog, there is look better
class GPGDialog(Adw.AlertDialog):
    def __init__(self, win: MainWindow, key_values: tuple):
        super().__init__()
        (
            pkg_id,
            userid,
            hexkeyid,
            keyurl,
            timestamp,
        ) = key_values
        self.win = win
        self.set_content_width(800)
        self.set_content_height(800)
        self.set_follows_content_size(True)

        self.add_css_class("gpg_dialog")
        self.set_heading(_("Install GPG Key"))
        body = f"""
        User ID   : {userid}
        Key       : {pkg_id}
        """.lstrip()
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
        self.present(self.win)
        self._loop.run()


class YesNoDialog(Adw.AlertDialog):
    def __init__(self, win: MainWindow, text: str, title: str):
        super().__init__()
        self.win = win
        self.answer = False
        self.set_content_width(800)
        self.set_content_height(800)
        self.set_follows_content_size(True)

        self.set_heading(title)
        self.set_body(text)
        self._loop = GLib.MainLoop()
        self.add_response("yes", _("Yes"))
        self.set_response_appearance("yes", Adw.ResponseAppearance.DESTRUCTIVE)
        self.add_response("no", _("No"))
        self.set_default_response("no")
        self.set_close_response("no")
        self.connect("response", self.response)

    def response(self, dialog, result, *args):
        self.answer = result == "yes"
        self._loop.quit()
        self.close()

    def show(self):
        self.present(self.win)
        self._loop.run()
