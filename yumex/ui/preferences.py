from gi.repository import Gtk, Adw

from yumex.constants import rootdir
from yumex.utils import log  # noqa: F401


@Gtk.Template(resource_path=f"{rootdir}/ui/preferences.ui")
class YumexPreferences(Adw.PreferencesWindow):
    __gtype_name__ = "YumexPreferences"

    pref_setting_01 = Gtk.Template.Child()
    pref_setting_02 = Gtk.Template.Child()
    pref_setting_03 = Gtk.Template.Child()

    repo_group = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win = win
        self.setting = win.settings
        self.setup()

    def setup(self):
        flags = ["pref_setting_01", "pref_setting_02", "pref_setting_03"]
        for flag in flags:
            pref = flag.replace("_", "-")
            state = self.setting.get_boolean(pref)
            switch = getattr(self, flag)
            switch.set_active(state)
            switch.connect("state-set", self.on_setting_changed, pref)
        # get repositories and add them
        repos = self.win.package_view.backend.get_repositories()
        for id, name, enabled in repos:
            repo_widget = YumexRepository()
            repo_widget.set_title(id)
            repo_widget.set_subtitle(name)
            repo_widget.enabled.set_state(enabled)
            self.repo_group.add(repo_widget)

    def on_setting_changed(self, widget, state, setting):
        log(f"setting {setting} is changed to {state}")
        self.setting.set_boolean(setting, state)


@Gtk.Template(resource_path=f"{rootdir}/ui/repository.ui")
class YumexRepository(Adw.ActionRow):
    __gtype_name__ = "YumexRepository"

    enabled = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
