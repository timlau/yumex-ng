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
# Copyright (C) 2023  Tim Lauridsen
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yumex.ui.window import YumexMainWindow

from gi.repository import Gtk

from yumex.constants import ROOTDIR
from yumex.utils import log
from yumex.utils.enums import PackageFilter, SortType, InfoType


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/package_settings.ui")
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
        self.win: YumexMainWindow = win
        self.setting = win.settings
        self.current_pkg_filter: PackageFilter = None
        self.previuos_pkg_filter: PackageFilter = None
        self.show_icon.set_from_icon_name("diagnostics-symbolic")
        self.sort_icon.set_from_icon_name("view-sort-descending-rtl-symbolic")

    def set_focus(self):
        self.installed_row.grab_focus()

    def set_active_filter(self, pkg_filter: PackageFilter):
        match pkg_filter:
            case PackageFilter.UPDATES:
                self.filter_updates.activate()
            case PackageFilter.INSTALLED:
                self.filter_installed.activate()
            case PackageFilter.AVAILABLE:
                self.filter_available.activate()

    def unselect_all(self):
        self.filter_available.set_active(False)
        self.filter_installed.set_active(False)
        self.filter_updates.set_active(False)
        self.filter_search.set_active(True)

    def get_info_type(self) -> InfoType:
        selected = self.info_type.get_selected()
        return list(InfoType)[selected]

    def get_sort_attr(self) -> SortType:
        selected = self.sort_by.get_selected()
        return list(SortType)[selected]

    @Gtk.Template.Callback()
    def on_sorting_activated(self, widget):
        log(f"Sorting activated: {widget}")

    def on_package_filter_activated(self, button):
        entry = self.win.search_bar.get_child()
        entry.set_text("")
        pkg_filter: PackageFilter = PackageFilter(button.get_name())
        self.win.package_view.get_packages(pkg_filter)
        self.current_pkg_filter = pkg_filter
        self.previuos_pkg_filter = pkg_filter

    @Gtk.Template.Callback()
    def on_info_type_selected(self, widget, data):
        """capture the Notify for the selected property is changed"""
        log(f"package info changed {self.info_type.get_selected()}")
        self.win.package_view.on_selection_changed(
            self.win.package_view.get_model(), 0, 0
        )
        self.win.sidebar.set_reveal_flap(False)

    @Gtk.Template.Callback()
    def on_sort_by_selected(self, widget, data):
        """capture the Notify for the selected property is changed"""
        log(f"sort_by changed {self.sort_by.get_selected()}")
        self.win.package_view.sort()
        self.win.package_view.refresh()
        self.win.sidebar.set_reveal_flap(False)
