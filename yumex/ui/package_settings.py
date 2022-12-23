# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2022  Tim Lauridsen

from gi.repository import Gtk

from yumex.constants import rootdir
from yumex.utils import log  # noqa: F401


@Gtk.Template(resource_path=f"{rootdir}/ui/package_settings.ui")
class YumexPackageSettings(Gtk.Box):
    __gtype_name__ = "YumexPackageSettings"

    filter_available = Gtk.Template.Child()
    filter_installed = Gtk.Template.Child()
    filter_updates = Gtk.Template.Child()
    filter_search = Gtk.Template.Child()
    sort_by = Gtk.Template.Child()
    info_type = Gtk.Template.Child()
    show_icon = Gtk.Template.Child()
    sort_icon = Gtk.Template.Child()
    installed_row = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win = win
        self.setting = win.settings
        self.current_pkg_filter = None
        self.previuos_pkg_filter = None
        self.show_icon.set_from_icon_name("diagnostics-symbolic")
        self.sort_icon.set_from_icon_name("view-sort-descending-rtl-symbolic")

    def set_focus(self):
        self.installed_row.grab_focus()

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
        self.filter_search.set_active(True)

    def get_info_type(self):
        selected = self.info_type.get_selected()
        return ["description", "files", "update_info"][selected]

    def get_sort_attr(self):
        selected = self.sort_by.get_selected()
        return ["name", "arch", "size", "repo"][selected]

    @Gtk.Template.Callback()
    def on_sorting_activated(self, widget):
        log(f"Sorting activated: {widget}")

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
        self.current_pkg_filter = pkg_filter
        self.previuos_pkg_filter = pkg_filter

    @Gtk.Template.Callback()
    def on_info_type_notify(self, widget, data):
        """capture the Notify for the selected property is changed"""
        match data.name:
            case "selected":
                log(f"package info changed {self.info_type.get_selected()}")
                self.win.package_view.on_selection_changed(
                    self.win.package_view.get_model(), 0, 0
                )
                self.win.sidebar.set_reveal_flap(False)

    @Gtk.Template.Callback()
    def on_sort_by_notify(self, widget, data):
        """capture the Notify for the selected property is changed"""
        match data.name:
            case "selected":
                log(f"sort_by changed {self.sort_by.get_selected()}")
                self.win.package_view.sort()
                self.win.package_view.refresh()
                self.win.sidebar.set_reveal_flap(False)
