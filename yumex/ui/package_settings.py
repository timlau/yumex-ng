from gi.repository import Gtk

from yumex.constants import rootdir
from yumex.utils import log  # noqa: F401


@Gtk.Template(resource_path=f"{rootdir}/ui/package_settings.ui")
class YumexPackageSettings(Gtk.Box):
    __gtype_name__ = "YumexPackageSettings"

    filter_available = Gtk.Template.Child()
    filter_installed = Gtk.Template.Child()
    filter_updates = Gtk.Template.Child()
    sort_by = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win = win
        self.setting = win.settings
        self.current_pkg_filter = None
        self.previuos_pkg_filter = None

    def set_active_filter(self, pkg_filter):
        match pkg_filter:
            case "updates":
                self.filter_updates.activate()
            case "installed":
                self.filter_installed.activate()
            case "available":
                self.filter_available.activate()

    def unselect_all(self):
        self.filter_available.set_active(False)
        self.filter_installed.set_active(False)
        self.filter_updates.set_active(False)

    def get_sort_attr(self):
        selected = self.sort_by.get_selected()
        return ["name", "arch", "size", "repo"][selected]

    @Gtk.Template.Callback()
    def on_sorting_activated(self, widget):
        log(f"Sorting activated: {widget}")

    @Gtk.Template.Callback()
    def on_package_filter_toggled(self, button):
        state = button.get_active()
        if state:
            log(f"name : {button.get_name()} state: {state}")
            self.on_package_filter_activated(button)

    def on_package_filter_activated(self, button):
        entry = self.win.search_bar.get_child()
        entry.set_text("")
        pkg_filter = button.get_name()
        match pkg_filter:
            case "available":
                self.win.package_view.get_packages("available")
            case "installed":
                self.win.package_view.get_packages("installed")
            case "updates":
                self.win.package_view.get_packages("updates")
            case _:
                log(f"package_filter not found : {pkg_filter}")
        self.current_pkg_filer = pkg_filter
        self.previuos_pkg_filer = pkg_filter
        # self.show_message(f"package filter : {item.get_name()} selected")
