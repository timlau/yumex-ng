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

from gi.repository import Gio, GObject, Gtk

from yumex.backend.dnf import YumexPackage
from yumex.backend.interface import Presenter
from yumex.constants import APP_ID, ROOTDIR
from yumex.ui import get_package_selection_tooltip
from yumex.ui.dialogs import error_dialog
from yumex.ui.queue_view import YumexQueueView
from yumex.utils import RunAsync, timed
from yumex.utils.enums import PackageFilter, PackageState, PackageTodo, SortType
from yumex.utils.storage import PackageStorage

logger = logging.getLogger(__name__)


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

    def __init__(self, presenter: Presenter, qview: YumexQueueView, **kwargs):
        super().__init__(**kwargs)
        self.presenter = presenter
        self.storage = PackageStorage()
        self.queue_view = qview
        self.sort_attr = SortType.NAME
        self.batch_selection = False
        self.settings = Gio.Settings(APP_ID)
        self.setup()

    def setup(self):
        """Setup the properties, there will be set again on a reset"""
        self.store = self.storage.clear()
        self.selection.set_model(self.store)
        self.last_position = -1
        self.last_selected = None
        self.column_num = 0

    def reset(self):
        """Reset the view"""
        logger.debug("Reset Package View")
        self.presenter.reset_cache()
        self.queue_view.reset()
        self.setup()

    def refresh(self):
        """refresh the view"""
        if len(self.store) > 0:
            self.selection.selection_changed(0, len(self.store))

    def get_packages(self, pkg_filter: PackageFilter):
        """fetch the packages and add them to the store"""

        def set_completed(pkgs: list, error=False):
            self.presenter.set_window_sesitivity(True)
            if not error:
                self.add_packages_to_store(pkgs)
                self.presenter.progress.hide()
            else:
                self.presenter.progress.hide()
                error_dialog(self.get_root(), "Error in loading packages", str(error))
            # refresh the package description for the selected package in the view
            if len(self.store) > 0:
                self.on_selection_changed(self.selection, 0, 0)

        logger.debug(f"Loading packages : {pkg_filter}")

        self.presenter.progress.set_title(_("Loading Packages"))
        self.presenter.progress.set_subtitle(_("This may take a little while"))

        self.presenter.progress.show()
        self.presenter.set_window_sesitivity(False)
        RunAsync(self.presenter.get_packages_by_filter, set_completed, pkg_filter)

    # @timed
    def search(self, txt, options={}):
        """search for packages and add them to store"""
        if len(txt) > 2:
            logger.debug(f"search packages field: value: {txt}")
            pkgs = self.presenter.get_packages(self.presenter.search(txt, options=options))
            self.add_packages_to_store(pkgs)

    @timed
    def add_packages_to_store(self, pkgs):
        """adding packages to store"""
        logger.debug("Adding packages to store")
        # create a new store and add packages (big speed improvement)
        self.storage.clear()
        # for pkg in sorted(pkgs, key=lambda n: n.name.lower()):

        for pkg in pkgs:
            if qpkg := self.queue_view.find_by_nevra(pkg.nevra):
                self.storage.add_package(qpkg)
            else:
                self.storage.add_package(pkg)
        logger.debug(f" --> sorting by : {self.sort_attr}")
        self.store = self.storage.sort_by(self.sort_attr)
        self.selection.set_model(self.store)
        logger.debug(f" --> number of packages : {len(list(pkgs))}")

    def sort(self, sort_attr: SortType):
        """Sort the packages in the store"""
        logger.debug(f" --> sorting by : {sort_attr}")
        self.sort_attr = sort_attr
        self.store = self.storage.sort_by(sort_attr)

    def set_styles(self, widget, pkg) -> None:
        """Set widget style based on pkg state"""
        current_styles = widget.get_css_classes()
        current_styles = [style for style in current_styles if style not in CLEAN_STYLES]
        match pkg.state:
            case PackageState.INSTALLED:
                current_styles.append("success")
            case PackageState.UPDATE:
                current_styles.append("error")
            case PackageState.DOWNGRADE:
                current_styles.append("warning")
        widget.set_css_classes(current_styles)

    def select_all(self, state: bool):
        self.batch_selection = True
        to_add = []
        to_delete = []
        for pkg in self.store:
            if state:
                if not pkg.queued:
                    self._set_queued(pkg, True, to_add)
            elif pkg.queued:
                self._set_queued(pkg, False, to_delete)
        if to_add:
            self.queue_view.add_packages(to_add)
        if to_delete:
            self.queue_view.remove_packages(to_delete)
        self.refresh()
        self.batch_selection = False
        return to_add, to_delete

    def _set_queued(self, pkg, is_queued: bool, to_list: list):
        pkg.queue_action = True
        pkg.queued = is_queued
        to_list.append(pkg)

    def toggle_selected(self):
        if len(self.store) > 0:
            pkg: YumexPackage = self.selection.get_selected_item()
            pkg.queued = not pkg.queued
            self.refresh()

    def on_package_action(self, action):
        """Handle action from the action bar"""
        pkg: YumexPackage = self.selection.get_selected_item()
        logger.debug(f"on_action: {action} on {pkg}")
        if pkg.is_installed:
            match action:
                case "downgrade":
                    pkg.todo = PackageTodo.DOWNGRADE
                case "reinstall":
                    pkg.todo = PackageTodo.REINSTALL
                case "distrosync":
                    pkg.todo = PackageTodo.DISTROSYNC
            self.queue_view.add_package(pkg)
            self.presenter.show_message(_(f"Package queued for {action}"))
        else:
            self.presenter.show_message(_(f"Package must be installed installed for {action}"))

    # --------------------- signals --------------------------------
    @GObject.Signal(arg_types=(object,))
    def selection_changed(self, pkg: YumexPackage):
        pass

    # --------------------- callbacks --------------------------------

    def on_queued_toggled(self, widget, item):
        """update the dataobject with the current check state"""
        pkg: YumexPackage = item.get_item()
        # log(f"toggled : {pkg}")
        if not pkg:
            return
        checkbox = item.get_child()
        tip = get_package_selection_tooltip(pkg)
        checkbox.set_tooltip_text(tip)
        # log(
        #     f"PackageView.on_queued_toggled : {pkg} dep: {pkg.is_dep} qa: {pkg.queue_action} bs: {self.batch_selection}"  # noqa
        # )
        # if a pkg is select as a dep, the the user can't deselect
        if pkg.is_dep:
            checkbox.set_sensitive(False)
        else:
            checkbox.set_sensitive(True)
        if pkg.queue_action:  # package is being processed by queue (add/remove)
            pkg.queue_action = False
        else:  # the user has clicked on the widget
            # log(
            #     f"PackageView.on_queued_toggled : {pkg} dep: {pkg.is_dep} qa: {pkg.queue_action} bs: {self.batch_selection}"  # noqa
            # )
            if not self.batch_selection:
                pkg.queued = widget.get_active()
                if pkg.queued:
                    self.queue_view.add_package(pkg)
                else:
                    self.queue_view.remove_package(pkg)

    @Gtk.Template.Callback()
    def on_selection_changed(self, widget, position, n_items):
        # dont send selection changed on batch changes, like select all
        if self.batch_selection:
            return
        if len(self.store) > 0:
            pkg: YumexPackage = self.selection.get_selected_item()
            if self.last_selected is None or pkg != self.last_selected:
                logger.debug(f"SIGNAL: emit selection_changed: {pkg}")
                self.emit("selection-changed", pkg)
                self.last_selected = pkg
        else:
            self.emit("selection-changed", None)
            self.last_selected = None

    # --------------------- Factory setup methods --------------------------------

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

    # --------------------- Factory bind methods --------------------------------

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
        check_button = item.get_child()  # Get the Gtk.Checkbutton stored in the ListItem
        pkg = item.get_item()  # get the model item, connected to current ListItem
        pkg.bind_property("queued", check_button, "active", GObject.BindingFlags.SYNC_CREATE)
        check_button.set_active(pkg.queued)  # Update Gtk.Label with data from model item
