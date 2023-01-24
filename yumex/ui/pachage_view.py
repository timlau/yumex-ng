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

from yumex.utils.storage import PackageStorage

if TYPE_CHECKING:
    from yumex.ui.window import YumexMainWindow

from gi.repository import Gtk
from yumex.backend.interface import Presenter

from yumex.constants import ROOTDIR
from yumex.backend.dnf import YumexPackage

# from yumex.backend.dnf import Backend, DnfCallback
from yumex.ui import get_package_selection_tooltip
from yumex.utils.enums import (
    InfoType,
    PackageFilter,
    PackageState,
    SearchField,
    SortType,
)
from yumex.utils import log, RunAsync, timed

CLEAN_STYLES = ["success", "error", "accent", "warning"]


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/package_view.ui")
class YumexPackageView(Gtk.ColumnView):
    __gtype_name__ = "YumexPackageView"

    names = Gtk.Template.Child("names")
    versions = Gtk.Template.Child("versions")
    repos = Gtk.Template.Child("repos")
    queued = Gtk.Template.Child()
    archs = Gtk.Template.Child()
    sizes = Gtk.Template.Child()
    descriptions = Gtk.Template.Child()

    selection = Gtk.Template.Child("selection")

    def __init__(self, win, presenter: Presenter, **kwargs):
        super().__init__(**kwargs)
        self.win: YumexMainWindow = win
        self.presenter = presenter
        self.storage = PackageStorage()
        self.setup()

    def setup(self):
        self.store = self.storage.clear()
        self.selection.set_model(self.store)
        self.last_position = -1
        self.column_num = 0
        self._last_selected_pkg: YumexPackage = None

    def reset(self):
        log("Reset Package View")
        self.queue_view.reset()
        self.setup()
        self.presenter.reset_backend()
        self.presenter.reset_cache()

    @property
    def queue_view(self):
        return self.win.queue_view

    def get_packages(self, pkg_filter: PackageFilter):
        def set_completed(result, error=False):
            self.win.main_view.set_sensitive(True)
            pkgs: list = result
            self.add_packages_to_store(pkgs)
            self.win.progress.hide()
            # hide package setting sidebar
            self.win.sidebar.set_reveal_flap(False)
            # refresh the package description for the selected package in the view
            self.on_selection_changed(self.selection, 0, 0)
            # restore focus to search entry
            if self.win.search_bar.get_search_mode():
                self.win.search_entry.grab_focus()

        log(f"Loading packages : {pkg_filter}")

        self.win.progress.set_title(_("Loading Packages"))
        self.win.progress.set_subtitle(_("This make take a little while"))

        self.win.progress.show()
        self.win.main_view.set_sensitive(False)
        RunAsync(self.presenter.get_packages_by_filter, set_completed, pkg_filter)

    # @timed
    def search(self, txt, field=SearchField.NAME):
        if len(txt) > 2:
            log(f"search packages field:{field} value: {txt}")
            pkgs = self.presenter.get_packages(
                self.presenter.search(txt, field=field, limit=1)
            )
            self.add_packages_to_store(pkgs)

    @timed
    def add_packages_to_store(self, pkgs):
        log("Adding packages to store")
        # create a new store and add packages (big speed improvement)
        self.storage.clear()
        # for pkg in sorted(pkgs, key=lambda n: n.name.lower()):

        for pkg in pkgs:
            if qpkg := self.queue_view.find_by_nevra(pkg.nevra):
                self.storage.add_package(qpkg)
            else:
                self.storage.add_package(pkg)
        sort_attr = self.win.package_settings.get_sort_attr()
        log(f" --> sorting by : {sort_attr}")
        self.store = self.storage.sort_by(sort_attr)
        self.selection.set_model(self.store)
        log(f" --> number of packages : {len(list(pkgs))}")

    def sort(self):
        sort_attr = SortType(self.win.package_settings.get_sort_attr())
        log(f" --> sorting by : {sort_attr}")
        self.store = self.storage.sort_by(sort_attr)

    def set_styles(self, widget, pkg) -> None:
        current_styles = widget.get_css_classes()
        current_styles = [
            style for style in current_styles if style not in CLEAN_STYLES
        ]
        match pkg.state:
            case PackageState.INSTALLED:
                current_styles.append("success")
            case PackageState.UPDATE:
                current_styles.append("error")
        widget.set_css_classes(current_styles)

    def select_all(self, state: bool):
        to_add = []
        to_delete = []
        for pkg in self.store:
            if state:
                if not pkg.queued:
                    self._extracted_from_select_all_7(pkg, True, to_add)
            elif pkg.queued:
                self._extracted_from_select_all_7(pkg, False, to_delete)
        if to_add:
            self.queue_view.add_packages(to_add)
        if to_delete:
            self.queue_view.remove_packages(to_add)
        self.refresh()

    # TODO Rename this here and in `select_all`
    def _extracted_from_select_all_7(self, pkg, arg1, arg2):
        pkg.queue_action = True
        pkg.queued = arg1
        arg2.append(pkg)

    def refresh(self):
        self.selection.selection_changed(0, len(self.store))

    def toggle_selected(self):
        if len(self.store) > 0:
            pkg: YumexPackage = self.selection.get_selected_item()
            pkg.queued = not pkg.queued
            self.refresh()

    @Gtk.Template.Callback()
    def on_package_column_checkmark_setup(self, widget, item):
        check = Gtk.CheckButton()
        check.connect("toggled", self.on_queued_toggled, item)
        check.set_can_focus(False)
        item.set_child(check)

    @Gtk.Template.Callback()
    def on_package_column_text_setup(self, widget, item):
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        label.set_margin_start(10)
        item.set_child(label)

    @Gtk.Template.Callback()
    def on_name_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        pkg = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, pkg)
        label.set_text(pkg.name)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_version_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        pkg = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, pkg)
        label.set_text(pkg.evr)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_repo_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        pkg = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, pkg)
        label.set_text(pkg.repo)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_arch_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        pkg = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, pkg)
        label.set_text(pkg.arch)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_size_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        pkg = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, pkg)
        label.set_text(pkg.size_with_unit)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_description_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        pkg = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, pkg)
        label.set_text(pkg.description)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_queued_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        pkg = item.get_item()  # get the model item, connected to current ListItem
        label.set_active(pkg.queued)  # Update Gtk.Label with data from model item

    def set_pkg_info(self, pkg):
        def completed(pkg_info, error=False):
            self.win.package_info.update(info_type, pkg_info)

        if self._last_selected_pkg and pkg == self._last_selected_pkg:
            return
        self._last_selected_pkg = pkg
        info_type = InfoType(self.win.package_settings.get_info_type())
        RunAsync(
            self.presenter.get_package_info,
            completed,
            pkg,
            info_type,
        )

    @Gtk.Template.Callback()
    def on_selection_changed(self, widget, position, n_items):
        if len(self.store) > 0:
            pkg: YumexPackage = self.selection.get_selected_item()
            self.set_pkg_info(pkg)
        else:
            self.win.package_info.clear()

    def on_queued_toggled(self, widget, item):
        """update the dataobject with the current check state"""
        pkg: YumexPackage = item.get_item()
        checkbox = item.get_child()
        tip = get_package_selection_tooltip(pkg)
        checkbox.set_tooltip_text(tip)
        # if a pkg is select as a dep, the the user can't deselect
        if pkg.is_dep:
            checkbox.set_sensitive(False)
        else:
            checkbox.set_sensitive(True)
        if pkg.queue_action:  # package is being processed by queue (add/remove)
            pkg.queue_action = False
        else:  # the user has clicked on the widget
            pkg.queued = widget.get_active()
            if pkg.queued:
                self.queue_view.add_package(pkg)
            else:
                self.queue_view.remove_package(pkg)
