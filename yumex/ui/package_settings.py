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
# Copyright (C) 2024 Tim Lauridsen

import logging

from gi.repository import Adw, GObject, Gtk

from yumex.constants import ROOTDIR
from yumex.utils.enums import InfoType, PackageFilter, SortType

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/package_settings.ui")
class YumexPackageSettings(Gtk.Box):
    __gtype_name__ = "YumexPackageSettings"

    filter_available: Gtk.CheckButton = Gtk.Template.Child()
    filter_installed: Gtk.CheckButton = Gtk.Template.Child()
    filter_updates: Gtk.CheckButton = Gtk.Template.Child()
    filter_search: Gtk.CheckButton = Gtk.Template.Child()
    sort_by: Adw.ComboRow = Gtk.Template.Child()
    info_type: Adw.ComboRow = Gtk.Template.Child()
    installed_row: Adw.ActionRow = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_pkg_filter: PackageFilter = None
        self.previuos_pkg_filter: PackageFilter = None

    def set_focus(self):
        """Set focus on the settings sidebar."""
        self.installed_row.grab_focus()

    def set_active_filter(self, pkg_filter: PackageFilter):
        """Set the active package filter"""
        match pkg_filter:
            case PackageFilter.UPDATES:
                self.filter_updates.activate()
            case PackageFilter.INSTALLED:
                self.filter_installed.activate()
            case PackageFilter.AVAILABLE:
                self.filter_available.activate()

    def unselect_all(self):
        """Unselect all filters, so we can re-select one"""
        self.previuos_pkg_filter = None
        self.filter_available.set_active(False)
        self.filter_installed.set_active(False)
        self.filter_updates.set_active(False)
        self.filter_search.set_active(True)

    def get_info_type(self) -> InfoType:
        """get the current info type"""
        selected = self.info_type.get_selected()
        return list(InfoType)[selected]

    def get_sort_attr(self) -> SortType:
        """get the current sort attribute"""
        selected = self.sort_by.get_selected()
        return list(SortType)[selected]

    def on_package_filter_activated(self, button):
        """handler for package filter changes"""
        pkg_filter: PackageFilter = PackageFilter(button.get_name())
        self.current_pkg_filter = pkg_filter
        if self.current_pkg_filter != self.previuos_pkg_filter:
            self.previuos_pkg_filter = pkg_filter
            logger.debug(f"SIGNAL: emit package-filter-changed: {pkg_filter}")
            self.emit("package-filter-changed", pkg_filter)

    @Gtk.Template.Callback()
    def on_info_type_selected(self, widget, data):
        """capture the Notify for the selected property is changed"""
        info_type = self.get_info_type()
        logger.debug(f"SIGNAL: emit info-type-changed: {info_type}")
        self.emit("info-type-changed", info_type)

    @Gtk.Template.Callback()
    def on_sort_by_selected(self, widget, data):
        """capture the Notify for the selected property is changed"""
        logger.debug(f"sort_by changed {self.sort_by.get_selected()}")
        sort_attr = self.get_sort_attr()
        logger.debug(f"SIGNAL: emit sort-arre-changed: {sort_attr}")
        self.emit("sort-attr-changed", sort_attr)

    @GObject.Signal(arg_types=(str,))
    def package_filter_changed(self, pkg_filter: PackageFilter):
        """signal emitted when a package filter is changed"""
        pass

    @GObject.Signal(arg_types=(str,))
    def sort_attr_changed(self, sort_attr: SortType):
        """signal emitted when a sort attribute is changed"""
        pass

    @GObject.Signal(arg_types=(str,))
    def info_type_changed(self, info_type: InfoType):
        """signal emitted when a info type is changed"""
        pass
