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

from gi.repository import Adw, Gio, Gtk

from yumex.constants import APP_ID, ROOTDIR
from yumex.utils.enums import FlatpakLocation

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/preferences.ui")
class YumexPreferences(Adw.PreferencesDialog):
    __gtype_name__ = "YumexPreferences"

    fp_remote: Adw.ComboRow = Gtk.Template.Child()
    fp_location: Adw.ComboRow = Gtk.Template.Child()

    md_period = Gtk.Template.Child()
    repo_group = Gtk.Template.Child()

    updater = Gtk.Template.Child()
    upd_custom = Gtk.Template.Child()
    upd_interval = Gtk.Template.Child()
    upd_show = Gtk.Template.Child()
    upd_notification = Gtk.Template.Child()
    upd_dark_icon = Gtk.Template.Child()

    def __init__(self, presenter, **kwargs):
        super().__init__(**kwargs)
        self.presenter = presenter
        self.settings = Gio.Settings(APP_ID)
        self._repos = []
        self.connect("unrealize", self.save_settings)
        self.setup_repo()
        self.setup_flatpak()
        self.setup_metadata()
        self.setup_updater()
        self.updater.set_visible(True)

    def setup_repo(self, show_all=False):
        # get repositories and add them
        repos = self.presenter.get_repositories()
        for id, name, enabled, prio in repos:
            if not show_all and (id.endswith("-debuginfo") or id.endswith("-source")):
                continue
            repo_widget = YumexRepository()
            repo_widget.set_title(id)
            repo_widget.set_subtitle(f"{name}( {prio})")
            repo_widget.enabled.set_state(enabled)
            self.repo_group.add(repo_widget)
            self._repos.append(repo_widget)

    def clear_repo(self):
        """clear all repositories"""
        for repo in self._repos:
            self.repo_group.remove(repo)
        self._repos = []

    def setup_updater(self):
        self.upd_custom.set_text(self.settings.get_string("upd-custom"))
        self.upd_interval.set_text(str(self.settings.get_int("upd-interval") // 60))
        self.upd_show.set_active(self.settings.get_boolean("upd-show-icon"))
        self.upd_show.set_state(self.settings.get_boolean("upd-show-icon"))
        self.upd_notification.set_active(self.settings.get_boolean("upd-notification"))
        self.upd_notification.set_state(self.settings.get_boolean("upd-notification"))
        self.upd_dark_icon.set_active(self.settings.get_boolean("upd-dark-icon"))
        self.upd_dark_icon.set_state(self.settings.get_boolean("upd-dark-icon"))

    def setup_metadata(self):
        period = self.settings.get_int("meta-load-periode")
        self.md_period.set_text(str(period // 60))

    def setup_flatpak(self):
        location = FlatpakLocation(self.settings.get_string("fp-location").lower())
        remote = self.settings.get_string("fp-remote")
        logger.debug(f" settings : {location=}")
        logger.debug(f" settings : {remote=}")
        self.set_selected_location(location)
        self.update_remote(location)

    def get_current_location(self) -> FlatpakLocation:
        return FlatpakLocation(self.fp_location.get_selected_item().get_string())

    def get_current_remote(self) -> FlatpakLocation:
        selected = self.fp_remote.get_selected_item()
        if selected:
            remote = selected.get_string()
        else:
            remote = None
        return remote

    def set_selected_location(self, current_location):
        for ndx, location in enumerate(self.fp_location.get_model()):
            if location.get_string() == current_location:
                self.fp_location.set_selected(ndx)
                break

    def save_settings(self, *args):
        location = self.get_current_location()
        self.settings.set_string("fp-location", location.value)
        remote = self.get_current_remote()
        if remote:
            self.settings.set_string("fp-remote", remote)
        try:
            period = int(self.md_period.get_text())
            self.settings.set_int("meta-load-periode", period * 60)
        except ValueError:
            pass
        # Updater Settings
        self.settings.set_string("upd-custom", self.upd_custom.get_text())
        try:
            self.settings.set_int("upd-interval", int(self.upd_interval.get_text()) * 60)
        except ValueError:
            pass
        self.settings.set_boolean("upd-show-icon", self.upd_show.get_state())
        self.settings.set_boolean("upd-notification", self.upd_notification.get_state())
        self.settings.set_boolean("upd-dark-icon", self.upd_dark_icon.get_state())
        return location, remote

    def update_remote(self, current_location) -> str | None:
        remotes = self.get_remotes(current_location)
        self.fp_remote.set_model(remotes)
        current_remote = self.settings.get_string("fp-remote")
        selected = None
        if not len(remotes):  # not remotes for current location
            self.fp_remote.set_sensitive(False)
            return selected

        self.fp_remote.set_sensitive(True)
        for ndx, remote in enumerate(self.fp_remote.get_model()):
            if remote.get_string() == current_remote:
                self.fp_remote.set_selected(ndx)
                selected = current_remote
                break
        if not selected:  # if current_remote not found, select first remote
            self.fp_remote.set_selected(0)
            selected = self.fp_remote.get_selected_item().get_string()
        return selected

    def get_remotes(self, location: FlatpakLocation) -> list:
        remotes = self.presenter.flatpak_backend.get_remotes(location=location)
        model = Gtk.StringList.new()
        if not remotes:
            logger.debug(f"pref: No remotes found location {location}")
            return model
        for remote in remotes:
            model.append(remote)
        return model

    @Gtk.Template.Callback()
    def on_location_selected(self, widget, data):
        """capture the Notify for the selected property is changed"""
        location = FlatpakLocation(self.fp_location.get_selected_item().get_string())
        self.update_remote(location)

    @Gtk.Template.Callback()
    def on_repo_source_debuginfo(self, widget, data):
        """repo_source_debuginfo callback"""
        logger.debug(f"on_repo_source_debuginfo {widget.get_state()}")
        self.clear_repo()
        self.setup_repo(show_all=not widget.get_state())


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/repository.ui")
class YumexRepository(Adw.ActionRow):
    __gtype_name__ = "YumexRepository"

    enabled = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
