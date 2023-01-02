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

from gi.repository import Gtk, Adw

from yumex.constants import rootdir
from yumex.utils import log


@Gtk.Template(resource_path=f"{rootdir}/ui/preferences.ui")
class YumexPreferences(Adw.PreferencesWindow):
    __gtype_name__ = "YumexPreferences"

    fp_source = Gtk.Template.Child()
    fp_location = Gtk.Template.Child()

    repo_group = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win = win
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
        source = self.settings.get_string("fp-source")
        log(f" settings : {location=}")
        log(f" settings : {source=}")
        self.set_location(location)
        self.set_source(location, source)

    def set_location(self, fp_location):
        ndx = 0
        for location in self.fp_location.get_model():
            if location.get_string() == fp_location:
                self.fp_location.set_selected(ndx)
                break
            ndx += 1

    def set_source(self, fp_location, fp_source):
        self.fp_source.set_model(self.get_remotes(fp_location))
        ndx = 0
        for source in self.fp_source.get_model():
            if source.get_string() == fp_source:
                self.fp_source.set_selected(ndx)
                break
            ndx += 1

    def get_remotes(self, location):
        if location == "system":
            system = True
        else:
            system = False
        remotes = self.win.flatpak_view.backend.get_remotes(location=system)
        model = Gtk.StringList.new()
        for remote in remotes:
            model.append(remote)
        return model

    def on_setting_changed(self, widget, state, setting):
        log(f"setting {setting} is changed to {state}")
        self.settings.set_boolean(setting, state)

    @Gtk.Template.Callback()
    def on_location_notify(self, widget, data):
        """capture the Notify for the selected property is changed"""
        match data.name:
            case "selected":
                location = self.fp_location.get_selected_item().get_string()
                source = self.settings.get_string("fp-source")
                self.settings.set_string("fp-location", location)
                self.set_source(location, source)

    @Gtk.Template.Callback()
    def on_source_notify(self, widget, data):
        """capture the Notify for the selected property is changed"""
        match data.name:
            case "selected":
                source = self.fp_source.get_selected_item().get_string()
                self.settings.set_string("fp-source", source)


@Gtk.Template(resource_path=f"{rootdir}/ui/repository.ui")
class YumexRepository(Adw.ActionRow):
    __gtype_name__ = "YumexRepository"

    enabled = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
