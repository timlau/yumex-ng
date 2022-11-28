from gi.repository import Gtk, Adw

from yumex.constants import rootdir


@Gtk.Template(resource_path=f"{rootdir}/ui/package_row.ui")
class YumexPackageRow(Adw.ActionRow):
    __gtype_name__ = "YumexPackageRow"

    def __init__(self, name, desc, **kwargs):
        super().__init__(**kwargs)

        self.set_name(name)
        self.set_title(name)
        self.set_subtitle(desc)
