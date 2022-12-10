from gi.repository import Gtk, Adw

from yumex.constants import rootdir
from yumex.utils import log  # noqa: F401


@Gtk.Template(resource_path=f"{rootdir}/ui/preferences.ui")
class YumexPreferences(Adw.PreferencesWindow):
    __gtype_name__ = "YumexPreferences"

    pref_setting_01 = Gtk.Template.Child()
    pref_setting_02 = Gtk.Template.Child()
    pref_setting_03 = Gtk.Template.Child()

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

    def on_setting_changed(self, widget, state, setting):
        log(f"setting {setting} is changed to {state}")
        self.setting.set_boolean(setting, state)
