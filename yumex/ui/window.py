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
# Copyright (C) 2025 Tim Lauridsen

import logging
from pathlib import Path

from gi.repository import Adw, Gio, Gtk  # type: ignore

from yumex.backend import TransactionResult
from yumex.backend.dnf import TransactionOptions, YumexPackage
from yumex.backend.presenter import YumexPresenter
from yumex.constants import APP_ID, PACKAGE_COLUMNS, ROOTDIR
from yumex.ui.advanced_actions import YumexAdvancedActions
from yumex.ui.dialogs import GPGDialog, YesNoDialog
from yumex.ui.flatpak_result import YumexFlatpakResult
from yumex.ui.flatpak_view import YumexFlatpakView
from yumex.ui.package_info import YumexPackageInfo
from yumex.ui.package_settings import YumexPackageSettings
from yumex.ui.package_view import YumexPackageView
from yumex.ui.progress import YumexProgress
from yumex.ui.queue_view import YumexQueueView
from yumex.ui.search_settings import YumexSearchSettings
from yumex.ui.transaction_result import YumexTransactionResult
from yumex.utils import BUILD_TYPE, RunAsync, get_distro_release
from yumex.utils.enums import InfoType, PackageFilter, Page, SortType, TransactionCommand
from yumex.utils.updater import sync_updates

logger = logging.getLogger(__name__)


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
    search_bar: Gtk.SearchBar = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    sidebar_button = Gtk.Template.Child("sidebar-button")
    package_paned = Gtk.Template.Child()
    update_info_box = Gtk.Template.Child()
    apply_button = Gtk.Template.Child()
    packages_page = Gtk.Template.Child()
    queue_page = Gtk.Template.Child()
    flatpaks_page = Gtk.Template.Child()
    flatpak_update_all: Gtk.Button = Gtk.Template.Child()
    package_menu = Gtk.Template.Child()
    package_action_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = kwargs["application"]
        self.settings = Gio.Settings(APP_ID)
        self.search_settings = YumexSearchSettings()
        self.current_pkg_filer = None
        self.previuos_pkg_filer = None
        self._last_selected_pkg: YumexPackage = None
        self.info_type: InfoType = InfoType.DESCRIPTION
        self._last_filter: PackageFilter | None = None
        self._resetting = False
        self.search_bar.connect_entry(self.search_entry)

        # save settings on windows close
        self.connect("unrealize", self.on_window_close)
        # connect to changes on Adw.ViewStack
        self.stack.get_pages().connect("selection-changed", self.on_stack_changed)
        self.presenter = YumexPresenter(self)
        # Setup Advanced actions dialog
        self.advanced_actions = YumexAdvancedActions(self)
        self.advanced_actions.connect("action", self.on_advanced_actions)
        self.setup_gui()

    @property
    def active_page(self) -> Page:
        return Page(self.stack.get_visible_child_name())

    def on_window_close(self, *args):
        """Save windows and column information on windows close"""
        self.presenter.package_backend.close()
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
        sync_updates()

    def setup_gui(self):
        """Setup the gui"""
        if BUILD_TYPE == "debug":
            self.add_css_class("devel")

        self.progress = YumexProgress(self)
        self.setup_packages_and_queue()
        self.setup_flatpaks()
        self.popover = Gtk.PopoverMenu()
        self.popover.set_menu_model(self.package_menu)
        self.popover.set_has_arrow(False)
        self.popover.set_parent(self)

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
        self.package_view = YumexPackageView(self.presenter, self.queue_view)
        self.package_view.connect("selection-changed", self.on_package_selection_changed)
        self.content_packages.set_child(self.package_view)
        self.set_saved_setting()
        # setup package settings
        self.package_settings = YumexPackageSettings()
        self.package_settings.connect("package-filter-changed", self.on_package_filter_changed)
        self.package_settings.connect("info-type-changed", self.on_info_type_changed)
        self.package_settings.connect("sort-attr-changed", self.on_sort_attr_changed)
        self.sidebar.set_sidebar(self.package_settings)
        # setup package info
        self.package_info = YumexPackageInfo()
        self.update_info_box.append(self.package_info)
        # setup search
        # self.search_entry.connect("move-focus", lambda _: True)

    def set_saved_setting(self):
        # set columns width from settings
        for setting in PACKAGE_COLUMNS:
            width = self.settings.get_int(f"col-{setting}-width")
            getattr(self.package_view, f"{setting}s").set_fixed_width(width)
        # set the package page clamp width
        clamp_width = self.settings.get_int("window-width")
        self.clamp_packages.set_maximum_size(clamp_width)
        self.clamp_packages.set_tightening_threshold(clamp_width - 100)
        self.package_paned.set_position(self.settings.get_int("pkg-paned-pos"))

    def on_queue_refresh(self, *args):
        """handle the refressh signal from queue view"""
        self.package_view.refresh()

    def show_message(self, title, timeout=5):
        """Create a toast with text and a given timeout"""
        toast = Adw.Toast(title=title)
        toast.set_timeout(timeout)
        self.toast_overlay.add_toast(toast)
        logger.debug(f"show_message : {title}")
        return toast

    def install_flatpakref(self, flatpakref):
        logger.debug(f"install flatpakref: {flatpakref}")
        self.select_page(Page.FLATPAKS)
        ref_file = Path(flatpakref)
        self.flatpak_view.install_flatpakref(ref_file)

    def install_rpmfile(self, rpmfile):
        logger.debug(f"install rpmfile: {rpmfile}")
        self.select_page(Page.PACKAGES)
        inst_file = Path(rpmfile).absolute()

        if not inst_file.exists():
            logger.debug(f"install rpmfile: {inst_file} not found")
            self.show_message(_(f"RPM file not found : {inst_file}"))
            return
        logger.debug(f"Execute the transaction on {inst_file}")
        opts = TransactionOptions(command=TransactionCommand.IS_FILE)
        result = self._do_transaction([inst_file.as_posix()], opts)
        logger.debug(f"Transaction execution ended : {result}")
        if result:  # transaction completed without issues\
            self.show_message(_("Transaction completed succesfully"), timeout=3)
            # reset everything
            self.reset_all()

    def show_flatpak_view(self):
        self.load_packages("installed")
        self.select_page(Page.FLATPAKS)

    def load_packages(self, pkg_filter: PackageFilter):
        """Helper for Trigger the activation of a given pkg filter"""
        self.package_settings.set_active_filter(pkg_filter)

    def set_sesitivity(self, sensitive: bool):
        """Set the sesitivity of the package view"""
        self.main_view.set_sensitive(sensitive)

    def _do_transaction(self, queued, opts: TransactionOptions):
        """execute the transaction with the root backend."""
        self.progress.show()
        self.progress.set_title(_("Building Transaction"))
        backend = self.presenter.package_backend
        # build the transaction
        result: TransactionResult = backend.build_transaction(queued, opts)
        self.progress.hide()
        if result.completed:
            # get confirmation
            transaction_result = YumexTransactionResult()
            if opts.offline:  # force offline transaction
                transaction_result.set_offline(True)
            transaction_result.show_result(result.data)
            if result.problems:
                transaction_result.set_problems(result.problems)
            if not result.data and not result.problems:
                transaction_result.show_errors(_("Nothing to do in this transaction"))
            transaction_result.show(self)
            if transaction_result.is_offline:
                opts.offline = True
            if transaction_result.confirm:
                # run the transaction
                while True:
                    self.progress.show()
                    if opts.offline:
                        self.progress.set_title(_("Building Offline Transaction"))
                    else:
                        self.progress.set_title(_("Running Transaction"))
                    result: TransactionResult = backend.run_transaction(opts)
                    if result.completed:
                        return True
                    if result.key_install and result.key_values:
                        self.progress.hide()
                        ok = self.confirm_gpg_import(result.key_values)
                        if ok:
                            logger.debug("Re-run transaction and import GPG keys")
                            # tell the backend to import this gpg key in next run
                            backend.do_gpg_import()
                            # rebuild the transaction again, before re-run
                            backend.build_transaction(queued, opts)
                            continue
                        else:
                            return True
                    else:
                        break
        if result.error:
            self.progress.hide()
            transaction_result = YumexTransactionResult()
            transaction_result.show_errors(result.error)
            transaction_result.show(self)

            # self.show_message(result.error)
        return False

    def confirm_gpg_import(self, key_values):
        dialog = GPGDialog(self, key_values)
        dialog.show()
        logger.debug(f"Install key: {dialog.install_key}")
        return dialog.install_key

    def confirm_flatpak_transaction(self, refs: list) -> bool:
        logger.debug("Window: confirm flatpak transaction")
        dialog = YumexFlatpakResult()
        dialog.populate(refs)
        dialog.show(self)
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
        RunAsync(self.presenter.get_package_info, completed, pkg, self.info_type)

    def on_clear_queue(self, *args):
        """app.clear_queue action handler"""
        self.queue_view.clear_all()

    def on_sidebar(self, *args):
        state = not self.sidebar.get_show_sidebar()
        self.sidebar.set_show_sidebar(state)
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
        if pkg:
            logger.debug(f"Window: package selection changed : {pkg}")
            self.set_pkg_info(pkg)

    def on_testing(self, *args):
        """Used to test gui stuff <Shift><Ctrl>T to activate"""
        print(1 / 0)

    def on_apply_actions_clicked(self, *_args):
        """handler for the apply button"""

        if queued := self.queue_view.get_queued():
            logger.debug(f"Execute the transaction on {len(queued)} packages")
            opts = TransactionOptions()
            result = self._do_transaction(queued, opts)
            logger.debug(f"Transaction execution ended : {result}")
            if result:  # transaction completed without issues\
                self.show_message(_("Transaction completed succesfully"), timeout=3)
                if opts.offline:
                    self.on_action_reboot()
                # reset everything
                self.reset_all()

    def reset_all(self):
        # reset everything
        self._resetting = True
        self.presenter.reset_backend()
        self.package_view.reset()
        self.package_settings.unselect_all()
        self.select_page(Page.PACKAGES)
        self.load_packages(PackageFilter.INSTALLED)
        self._resetting = False

    def do_search(self, text):
        # remove selection in package filter (sidebar)
        if not self._last_filter:
            self._last_filter = self.package_settings.current_pkg_filter
        self.package_settings.unselect_all()
        self.package_view.search(text, options=self.search_settings.options)

    def reset_search(self):
        # if self.package_settings.current_pkg_filter == PackageFilter.SEARCH:
        logger.debug("Reset search")
        # GLib.idle_add(self.load_packages, self._last_filter)
        self.load_packages(self._last_filter)
        self._last_filter = None

    @Gtk.Template.Callback()
    def on_search_changed(self, widget):
        """handler for changes in the seach entry"""
        search_txt = widget.get_text()
        logger.debug(f"search changed : {search_txt}")
        if search_txt == "" and not self._resetting:
            self.reset_search()
        elif search_txt != "":
            self.do_search(search_txt)
        return True

    @Gtk.Template.Callback()
    def on_search_activate(self, widget):
        """handler for enter pressed in the seach entry"""
        search_txt = widget.get_text()
        logger.debug(f"search activate : {search_txt}")
        if search_txt == "":
            self.reset_search()
        else:
            self.do_search(search_txt)
        return True

    @Gtk.Template.Callback()
    def on_search_settings(self, widget):
        options = self.search_settings.show(self)
        logger.debug(f"search settings : {options}")
        self.search_entry.grab_focus()
        self.on_search_activate(self.search_entry)

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
        self.package_action_button.set_sensitive(visible)

    def action_dispatch(self, action, *args):
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
            case "flatpak_search":
                self.flatpak_view.search()
            case "flatpak_update":
                if self.active_page == Page.FLATPAKS:
                    self.flatpak_view.update_all()
            case "flatpak_remove_unused":
                if self.active_page == Page.FLATPAKS:
                    self.flatpak_view.remove_unused()
            case "flatpak_runtime":
                if self.active_page == Page.FLATPAKS:
                    self.flatpak_view.show_runtime()
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
                    # dont select all when searching
                    if not self.search_bar.props.search_mode_enabled:
                        self.on_selectall_activate()
                    else:
                        # select all text in search entry
                        self.search_entry.select_region(0, 100)
            case "toggle_selection":
                if self.active_page == Page.PACKAGES:
                    self.package_view.toggle_selected()
            case "adv-actions":
                logger.debug("advanced actions")
                action = self.advanced_actions.show(self)
            case "downgrade" | "reinstall" | "distrosync":
                self.package_view.on_package_action(action.get_name())
            case other:
                logger.debug(f"ERROR: action: {other} not defined")
                raise ValueError(f"action: {other} not defined")

    def on_advanced_actions(self, widget, action, parameter):
        """handler for advanced actions"""
        logger.debug(f"advanced action: {action} parameter: {parameter}")
        match action:
            case "refresh-cache":
                self.on_action_expire_cache()
            case "system-upgrade":
                self.on_action_system_upgrade(parameter)
            case "cancel-system-upgrade":
                self.on_action_cancel_system_upgrade(parameter)
            case "reboot":
                self.on_action_reboot()
            case "distro-sync-system":
                self.on_action_distro_sync_system()
            case _:
                logger.debug(f"ERROR: action: {action} not defined")

    def on_action_reboot(self):
        """handler for reboot action"""
        self.progress.hide()
        logger.debug("offline transaction on reboot prepare")
        title = _("Offline transaction")
        msg = _("Do you want to prepare the offline transaction to be applied on next reboot ?")
        dialog = YesNoDialog(self, msg, title)
        dialog.show()
        if dialog.answer:
            rc = self.presenter.reboot_and_install()
            if rc:
                msg = _("Offline trasaction prepared to be applied on next reboot")
                self.show_message(msg)
            else:
                msg = _("Offline transaction prepare failed")
                self.show_message(msg)

    def on_action_expire_cache(self):
        def callback(*args):
            res, error = args[0]
            logger.debug(f"expire-cache: {res} : {error}")

            if res:
                self.reset_all()

        RunAsync(self.presenter.package_backend.client.clean, callback, "expire-cache")

    def on_action_system_upgrade(self, releasever):
        """handler for distro-sync action"""
        logger.debug(f"Execute system upgrade ({releasever})")
        current_release = get_distro_release()
        if releasever <= current_release:
            self.show_message(_("system upgrade target release must to larger than current release"))
            return
        opts = TransactionOptions(command=TransactionCommand.SYSTEM_UPGRADE, parameter=releasever, offline=True)
        result = self._do_transaction([], opts)
        logger.debug(f"Transaction execution ended : {result}")
        # we have to reset the backend to current releasever
        self.presenter.package_backend.reopen_session()
        self.progress.hide
        if result:  # transaction completed without issues\
            self.show_message(_("Offline Transaction completed succesfully"), timeout=3)
            self.on_action_reboot()
            # reset everything
            self.reset_all()

    def on_action_distro_sync_system(self):
        """handler for distro-sync action"""
        logger.debug("Execute distro-sync")
        opts = TransactionOptions(command=TransactionCommand.SYSTEM_DISTRO_SYNC)
        result = self._do_transaction([], opts)
        logger.debug(f"Transaction execution ended : {result}")
        if result:
            self.show_message(_("Distro-Sync completed succesfully"), timeout=3)
            # reset everything
            self.reset_all()

    def on_action_cancel_system_upgrade(self, releasever):
        """handler for offline transaction cancel action"""
        logger.debug(f"cancel offline transaction ({releasever})")
        res, errors = self.presenter.cancel_offline_transaction()
        if res:
            self.show_message(_("Offline transaction cancelled"), timeout=5)
        else:
            logger.debug(f"cancel offline transaction failed: {errors}")
            self.show_message(_("Offline transaction cancel failed"), timeout=5)

    def on_stack_changed(self, widget, position, n_items):
        """handler for stack page is changed"""
        logger.debug(f"stack changed : {self.active_page}")
        self.show_on_page()
        match self.active_page:
            case Page.PACKAGES:
                self.package_view.refresh()
            case Page.FLATPAKS:
                self.flatpak_view.refresh_need_attention()

    def on_package_filter_changed(self, widget, pkg_filter):
        logger.debug(f"SIGNAL: package filter changed : {pkg_filter}")
        # entry = self.search_bar.get_child()
        # entry.set_text("")
        pkg_filter = PackageFilter(pkg_filter)
        self.sidebar.set_show_sidebar(False)
        self.search_bar.set_search_mode(False)
        self.search_entry.delete_text(0, -1)
        self.package_view.get_packages(pkg_filter)

    def on_info_type_changed(self, widget, info_type: str):
        info_type = InfoType(info_type)
        logger.debug(f"SIGNAL: info-type-changed : {info_type}")
        self.info_type = info_type
        self.package_view.on_selection_changed(self.package_view.get_model(), 0, 0)
        self.sidebar.set_show_sidebar(False)

    def on_sort_attr_changed(self, widget, sort_attr: str):
        sort_attr = SortType(sort_attr)
        logger.debug(f"SIGNAL: sort-attr-changed : {sort_attr}")
        self.package_view.sort(sort_attr)
        self.package_view.refresh()
        self.sidebar.set_show_sidebar(False)

    def set_needs_attention(self, page: Page, num: int):
        """set the page needs_attention state"""
        state = num > 0
        match page:
            case Page.PACKAGES:
                self.packages_page.set_needs_attention(state)
            case Page.FLATPAKS:
                logger.debug(f"set_need_attetion (flatpak): state: {state} ")
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
