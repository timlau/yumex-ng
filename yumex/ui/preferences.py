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

from gi.repository import Gtk, Adw

from yumex.constants import ROOTDIR
from yumex.utils import log


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/preferences.ui")
class YumexPreferences(Adw.PreferencesWindow):
    __gtype_name__ = "YumexPreferences"

    fp_remote = Gtk.Template.Child()
    fp_location = Gtk.Template.Child()

    repo_group = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win: YumexMainWindow = win
        self.settings = win.settings
        self.setup()

    def setup(self):
        self.setup_flatpak()
        # get repositories and add them
        repos = self.win.package_view.backend.get_repositories()
        for id, name, enabled in repos:
            repo_widget = YumexRepository()
            repo_widget.set_title(id)
            repo_widget.set_subtitle(name)
            repo_widget.enabled.set_state(enabled)
            self.repo_group.add(repo_widget)

    def setup_flatpak(self):
        location = self.settings.get_string("fp-location")
        remote = self.settings.get_string("fp-remote")
        log(f" settings : {location=}")
        log(f" settings : {remote=}")
        self.set_location(location)
        self.set_remote(location, remote)

    def set_location(self, fp_location):
        for ndx, location in enumerate(self.fp_location.get_model()):
            if location.get_string() == fp_location:
                self.fp_location.set_selected(ndx)
                break

    def set_remote(self, fp_location, fp_remote):
        self.fp_remote.set_model(self.get_remotes(fp_location))
        for ndx, remote in enumerate(self.fp_remote.get_model()):
            if remote.get_string() == fp_remote:
                self.fp_remote.set_selected(ndx)
                break

    def get_remotes(self, location):
        system = location == "system"
        remotes = self.win.flatpak_view.backend.get_remotes(location=system)
        model = Gtk.StringList.new()
        for remote in remotes:
            model.append(remote)
        return model

    def on_setting_changed(self, widget, state, setting):
        log(f"setting {setting} is changed to {state}")
        self.settings.set_boolean(setting, state)

    @Gtk.Template.Callback()
    def on_location_selected(self, widget, data):
        """capture the Notify for the selected property is changed"""
        location = self.fp_location.get_selected_item().get_string()
        remote = self.settings.get_string("fp-remote")
        self.settings.set_string("fp-location", location)
        self.set_remote(location, remote)

    @Gtk.Template.Callback()
    def on_remote_selected(self, widget, data):
        """capture the Notify for the selected property is changed"""
        remote = self.fp_remote.get_selected_item().get_string()
        self.settings.set_string("fp-remote", remote)


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/repository.ui")
class YumexRepository(Adw.ActionRow):
    __gtype_name__ = "YumexRepository"

    enabled = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
