from gi.repository import Gtk, Adw, GLib, GObject, Gio

from yumex.constants import rootdir
from yumex.utils import log
from yumex.utils.enums import FlatpakAction


class ResultElem(GObject.GObject):
    def __init__(self, ref: str, action: FlatpakAction, source: str) -> None:
        super().__init__()
        self.ref: str = ref
        self.action: FlatpakAction = action
        self.source: str = source

    def __str__(self) -> str:
        match self.action:
            case FlatpakAction.INSTALL:
                action_str = _("Installing")
            case FlatpakAction.UNINSTALL:
                action_str = _("Unnstalling")
            case _:
                action_str = _("Updateing")
        return f"{action_str} <b>{self.ref}</b> <small>({self.source})</small>"


@Gtk.Template(resource_path=f"{rootdir}/ui/flatpak_result.ui")
class YumexFlatpakResult(Adw.Window):
    __gtype_name__ = "YumexFlatpakResult"

    result_view = Gtk.Template.Child()
    selection = Gtk.Template.Child()
    result_factory = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win = win
        self.confirm = False
        self._loop = GLib.MainLoop()
        self.store = Gio.ListStore.new(ResultElem)
        self.selection.set_model(self.store)

    def show(self):
        self.set_transient_for(self.win)
        self.present()
        self._loop.run()

    def populate(self, results: list[str, FlatpakAction, str]):
        for (ref, action, source) in results:
            elem = ResultElem(ref, action, source)
            log(f" --> Adding element {elem}")
            self.store.append(elem)

    @Gtk.Template.Callback()
    def on_confirm_clicked(self, button):
        self._loop.quit()
        self.confirm = True
        self.close()

    @Gtk.Template.Callback()
    def on_cancel_clicked(self, button):
        self._loop.quit()
        self.close()

    @Gtk.Template.Callback()
    def on_setup(self, widget, item):
        """Setup the widget to show in the Gtk.Listview"""
        label = Gtk.Label()
        label.set_xalign(0.0)
        item.set_child(label)

    @Gtk.Template.Callback()
    def on_bind(self, widget, item):
        """bind data from the store object to the widget"""
        label = item.get_child()
        obj: ResultElem = item.get_item()
        label.set_markup(str(obj))
