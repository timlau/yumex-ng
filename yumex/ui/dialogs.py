from gi.repository import Adw


def error_dialog(win, title: str, msg: str):
    def response(dialog, result, *args):
        # try:
        #     clb = win.get_clipboard()
        #     clb.set_text(msg)
        # except Exception as e:
        #     print(e)
        # finally:
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
