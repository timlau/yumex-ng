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

import re

from gi.repository import Gtk, Adw, Gio

from yumex.backend.daemon import TransactionResult, YumexRootBackend
from yumex.backend.dnf import YumexPackage
from yumex.backend.presenter import YumexPresenter
from yumex.constants import ROOTDIR, APP_ID, PACKAGE_COLUMNS
from yumex.ui.flatpak_result import YumexFlatpakResult
from yumex.ui.flatpak_view import YumexFlatpakView
from yumex.ui.pachage_view import YumexPackageView
from yumex.ui.queue_view import YumexQueueView
from yumex.ui.package_settings import YumexPackageSettings
from yumex.ui.progress import YumexProgress
from yumex.ui.package_info import YumexPackageInfo
from yumex.ui.transaction_result import YumexTransactionResult
from yumex.utils import RunAsync, log
from yumex.utils.enums import InfoType, PackageFilter, SearchField, Page, SortType


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/window.ui")
class YumexMainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "YumexMainWindow"

    content_packages = Gtk.Template.Child()
    clamp_packages = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    main_view = Gtk.Template.Child()
    content_groups = Gtk.Template.Child()
    content_queue = Gtk.Template.Child()
    content_flatpaks = Gtk.Template.Child()
    main_menu = Gtk.Template.Child("main-menu")
    sidebar = Gtk.Template.Child()
    stack = Gtk.Template.Child("view_stack")
    search_button = Gtk.Template.Child()
    search_bar = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    sidebar_button = Gtk.Template.Child("sidebar-button")
    package_paned = Gtk.Template.Child()
    update_info_box = Gtk.Template.Child()
    apply_button = Gtk.Template.Child()
    packages_page = Gtk.Template.Child()
    queue_page = Gtk.Template.Child()
    flatpaks_page = Gtk.Template.Child()
    flatpak_update_all: Gtk.Button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = kwargs["application"]
        self.settings = Gio.Settings(APP_ID)
        self.current_pkg_filer = None
        self.previuos_pkg_filer = None
        self.root_backend = None
        self._last_selected_pkg: YumexPackage = None
        self.info_type: InfoType = InfoType.DESCRIPTION

        # save settings on windows close
        self.connect("unrealize", self.save_window_props)
        # connect to changes on Adw.ViewStack
        self.stack.get_pages().connect("selection-changed", self.on_stack_changed)
        self.presenter = YumexPresenter(self)
        self.setup_gui()

    @property
    def active_page(self) -> Page:
        return Page(self.stack.get_visible_child_name())

    def save_window_props(self, *args):
        """Save windows and column information on windows close"""
        win_size = self.get_default_size()

        # Save windows size
        self.settings.set_int("window-width", win_size.width)
        self.settings.set_int("window-height", win_size.height)

        # Save coloumn widths
        for setting in PACKAGE_COLUMNS:
            width = getattr(self.package_view, f"{setting}s").get_fixed_width()
            width = self.settings.set_int(f"col-{setting}-width", width)

        self.settings.set_boolean("window-maximized", self.is_maximized())
        self.settings.set_boolean("window-fullscreen", self.is_fullscreen())
        self.settings.set_int("pkg-paned-pos", self.package_paned.get_position())

    def setup_gui(self):
        """Setup the gui"""
        self.progress = YumexProgress()
        self.progress.set_transient_for(self)
        self.setup_packages_and_queue()
        self.setup_flatpaks()

    def setup_flatpaks(self):
        self.flatpak_view = YumexFlatpakView(self.presenter)
        self.content_flatpaks.set_child(self.flatpak_view)

    def setup_packages_and_queue(self):
        """Setup the packages & queue pages"""
        # Setup queue page
        self.queue_view = YumexQueueView(self.presenter)
        self.queue_view.connect("refresh", self.on_queue_refresh)
        self.content_queue.set_child(self.queue_view)
        # setup packages page
        self.package_view = YumexPackageView(self, self.presenter, self.queue_view)
        self.package_view.connect(
            "selection-changed", self.on_package_selection_changed
        )
        self.content_packages.set_child(self.package_view)
        self.set_saved_setting()
        # setup package settings
        self.package_settings = YumexPackageSettings()
        self.package_settings.connect(
            "package-filter-changed", self.on_package_filter_changed
        )
        self.package_settings.connect("info-type-changed", self.on_info_type_changed)
        self.package_settings.connect("sort-attr-changed", self.on_sort_attr_changed)
        self.sidebar.set_flap(self.package_settings)
        # setup package info
        self.package_info = YumexPackageInfo()
        self.update_info_box.append(self.package_info)

    def set_saved_setting(self):
        # set columns width from settings and calc clamp width
        clamp_width = 100
        for setting in PACKAGE_COLUMNS:
            width = self.settings.get_int(f"col-{setting}-width")
            getattr(self.package_view, f"{setting}s").set_fixed_width(width)
            clamp_width += width
        self.clamp_packages.set_maximum_size(clamp_width)
        self.clamp_packages.set_tightening_threshold(clamp_width)
        self.package_paned.set_position(self.settings.get_int("pkg-paned-pos"))

    def on_queue_refresh(self, *args):
        """handle the refressh signal from queue view"""
        self.package_view.refresh()

    def show_message(self, title, timeout=2):
        """Create a toast with text and a given timeout"""
        toast = Adw.Toast(title=title)
        toast.set_timeout(timeout)
        self.toast_overlay.add_toast(toast)
        return toast

    def load_packages(self, pkg_filter: PackageFilter):
        """Helper for Trigger the activation of a given pkg filter"""
        self.package_settings.set_active_filter(pkg_filter)

    def set_sesitivity(self, sensitive: bool):
        """Set the sesitivity of the package view"""
        self.main_view.set_sensitive(sensitive)

    def _do_transaction(self, queued):
        """execute the transaction with the root backend."""
        self.progress.show()
        self.progress.set_title(_("Building Transaction"))
        with YumexRootBackend(self.presenter) as root_backend:
            # build the transaction
            result: TransactionResult = root_backend.build_transaction(queued)
            self.progress.hide()
            if result.completed:
                # get confirmation
                transaction_result = YumexTransactionResult()
                transaction_result.set_transient_for(self)
                transaction_result.show_result(result.data)
                transaction_result.show()
                if transaction_result.confirm:
                    # run the transaction
                    self.progress.show()
                    self.progress.set_title(_("Running Transaction"))
                    result: TransactionResult = root_backend.run_transaction()
                    if result.completed:
                        return True
            if result.error:
                self.show_message(result.error)
            return False

    def confirm_flatpak_transaction(self, refs: list) -> bool:
        log("Window: confirm flatpak transaction")
        dialog = YumexFlatpakResult()
        dialog.set_transient_for(self)
        dialog.populate(refs)
        dialog.show()
        confirm = dialog.confirm
        del dialog
        if confirm:
            self.progress.show()
            self.progress.set_title(_("Running Flatpak Transaction"))
        return confirm

    def set_pkg_info(self, pkg):
        def completed(pkg_info, error=False):
            self.package_info.update(self.info_type, pkg_info)

        if pkg is None:
            return self.package_info.clear()
        if self._last_selected_pkg and pkg == self._last_selected_pkg:
            return
        self._last_selected_pkg = pkg
        RunAsync(
            self.presenter.get_package_info,
            completed,
            pkg,
            self.info_type,
        )

    def on_clear_queue(self, *args):
        """app.clear_queue action handler"""
        self.queue_view.clear_all()

    def on_sidebar(self, *args):
        state = not self.sidebar.get_reveal_flap()
        self.sidebar.set_reveal_flap(state)
        if state:
            self.package_settings.set_focus()

    def on_filter_installed(self, *args):
        button = self.package_settings.filter_installed
        button.set_active(True)
        self.package_settings.on_package_filter_activated(button)

    def on_filter_updates(self, *args):
        button = self.package_settings.filter_updates
        button.set_active(True)
        self.package_settings.on_package_filter_activated(button)

    def on_filter_available(self, *args):
        button = self.package_settings.filter_available
        button.set_active(True)
        self.package_settings.on_package_filter_activated(button)

    def on_package_selection_changed(self, widget, pkg: YumexPackage):
        log(f"Window: package selection changed : {pkg}")
        self.set_pkg_info(pkg)

    def on_testing(self, *args):
        """Used to test gui stuff <Shift><Ctrl>T to activate"""
        pass

    def on_apply_actions_clicked(self, *_args):
        """handler for the apply button"""

        if queued := self.queue_view.get_queued():
            log(f"Execute the transaction on {len(queued)} packages")
            done = self._do_transaction(queued)
            log(f"Transaction execution ended : {done}")
            if done:  # transaction completed without issues
                # reset everything
                self.package_view.reset()
                self.search_bar.set_search_mode(False)
                self.show_message(_("Transaction completted succesfully"), timeout=3)
                self.load_packages(PackageFilter.INSTALLED)

    @Gtk.Template.Callback()
    def on_search_changed(self, widget):
        """handler for changes in the seach entry"""
        search_txt = widget.get_text()
        log(f"search changed : {search_txt}")
        if search_txt == "":
            if self.package_settings.current_pkg_filter == PackageFilter.SEARCH:
                # self.last_pkg_filer.activate()
                self.load_packages(self.package_settings.previuos_pkg_filter)
                return False
        elif search_txt[0] != ".":
            # remove selection in package filter (sidebar)
            self.package_settings.unselect_all()
            self.package_view.search(search_txt)
            self.package_settings.current_pkg_filter = PackageFilter.SEARCH

    @Gtk.Template.Callback()
    def on_search_activate(self, widget):
        """handler for enter pressed in the seach entry"""
        allowed_field_map = {
            "name": SearchField.NAME,
            "arch": SearchField.ARCH,
            "repo": SearchField.REPO,
            "desc": SearchField.SUMMARY,
        }
        search_txt = widget.get_text()
        log(f"search activate : {search_txt}")
        if search_txt[0] == ".":
            # syntax: .<field>=<value>
            cmds = re.compile(r"^\.(.*)=(.*)")
            res = cmds.match(search_txt)
            if len(res.groups()) == 2:
                field, key = res.groups()
                if field in allowed_field_map:
                    field = allowed_field_map[field]
                    self.package_settings.unselect_all()
                    log(f"searching for : {key} in pkg.{field}")
                    self.package_view.search(key, field=field)

        else:
            # remove selection in package filter (sidebar)
            self.package_settings.unselect_all()
            self.package_view.search(search_txt)
        self.package_settings.current_pkg_filter = PackageFilter.SEARCH

    def on_selectall_activate(self):
        """handler for select all on selection column right click menu"""
        # select all work only on updates pkg_filter
        if self.package_settings.current_pkg_filter in [
            PackageFilter.UPDATES,
            PackageFilter.SEARCH,
        ]:
            self.package_view.select_all(True)

    def on_deselectall_activate(self):
        """handler for deselect all on selection column right click menu"""
        match self.active_page:
            case Page.PACKAGES:
                self.package_view.select_all(False)
            case Page.QUEUE:
                self.queue_view.clear_all()

    def show_on_page(self):
        """show/hide widget dependend on the active page"""
        if self.active_page == Page.PACKAGES:
            self._set_vidgets_visibility(True)
        else:
            self._set_vidgets_visibility(False)
        # handle other page dependend widgets
        match self.active_page:
            case Page.PACKAGES | Page.QUEUE:
                self.apply_button.set_sensitive(True)
            case Page.FLATPAKS:
                self.apply_button.set_sensitive(False)

    def _set_vidgets_visibility(self, visible):
        self.search_button.set_sensitive(visible)
        self.search_bar.set_visible(visible)
        self.sidebar_button.set_sensitive(visible)

    def on_actions(self, action, *args):
        """Generic action dispatcher"""
        match action.get_name():
            case "page_one":
                self.stack.set_visible_child_name(Page.PACKAGES)
            case "page_two":
                self.stack.set_visible_child_name(Page.FLATPAKS)
            case "page_three":
                self.stack.set_visible_child_name(Page.QUEUE)
            case "apply_actions":
                if self.active_page in [Page.PACKAGES, Page.QUEUE]:
                    self.on_apply_actions_clicked()
            case "flatpak_remove":
                if self.active_page == Page.FLATPAKS:
                    self.flatpak_view.remove()
            case "flatpak_install":
                self.flatpak_view.install()
            case "flatpak_update":
                if self.active_page == Page.FLATPAKS:
                    self.flatpak_view.update_all()
            case "filter_installed":
                if self.active_page == Page.PACKAGES:
                    self.on_filter_installed()
            case "filter_updates":
                if self.active_page == Page.PACKAGES:
                    self.on_filter_updates()
            case "filter_available":
                if self.active_page == Page.PACKAGES:
                    self.on_filter_available()
            case "clear_queue":
                if self.active_page == Page.QUEUE:
                    self.on_clear_queue()
            case "sidebar":
                if self.active_page == Page.PACKAGES:
                    self.on_sidebar()
            case "deselect_all":
                if self.active_page in [Page.PACKAGES, Page.QUEUE]:
                    self.on_deselectall_activate()
            case "select_all":
                if self.active_page in [Page.PACKAGES, Page.QUEUE]:
                    self.on_selectall_activate()
            case "toggle_selection":
                if self.active_page == Page.PACKAGES:
                    self.package_view.toggle_selected()
            case other:
                log(f"ERROR: action: {other} not defined")
                raise ValueError(f"action: {other} not defined")

    def on_stack_changed(self, widget, position, n_items):
        """handler for stack page is changed"""
        log(f"stack changed : {self.active_page}")
        self.show_on_page()
        match self.active_page:
            case Page.PACKAGES:
                self.package_view.refresh()
            case Page.FLATPAKS:
                self.flatpak_view.refresh_need_attention()

    def on_package_filter_changed(self, widget, pkg_filter):
        log(f"SIGNAL: package filter changed : {pkg_filter}")
        entry = self.search_bar.get_child()
        entry.set_text("")
        pkg_filter = PackageFilter(pkg_filter)
        self.sidebar.set_reveal_flap(False)
        self.search_bar.set_search_mode(False)
        self.search_entry.set_text("")
        self.package_view.get_packages(pkg_filter)

    def on_info_type_changed(self, widget, info_type: str):
        info_type = InfoType(info_type)
        log(f"SIGNAL: info-type-changed : {info_type}")
        self.info_type = info_type
        self.package_view.on_selection_changed(self.package_view.get_model(), 0, 0)
        self.sidebar.set_reveal_flap(False)

    def on_sort_attr_changed(self, widget, sort_attr: str):
        sort_attr = SortType(sort_attr)
        log(f"SIGNAL: sort-attr-changed : {sort_attr}")
        self.package_view.sort(sort_attr)
        self.package_view.refresh()
        self.sidebar.set_reveal_flap(False)

    def set_needs_attention(self, page: Page, num: int):
        """set the page needs_attention state"""
        state = num > 0
        match page:
            case Page.PACKAGES:
                self.packages_page.set_needs_attention(state)
            case Page.FLATPAKS:
                log(f"set_need_attetion (flatpak): state: {state} ")
                self.flatpaks_page.set_needs_attention(state)
                if state:
                    self.flatpak_update_all.add_css_class("success")
                else:
                    self.flatpak_update_all.remove_css_class("success")
                self.flatpak_update_all.set_sensitive(state)

            case Page.GROUPS:
                pass
            case Page.QUEUE:
                self.queue_page.set_needs_attention(state)

    def select_page(self, page: Page):
        self.stack.set_visible_child_name(page)
