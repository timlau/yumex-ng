from distutils.command.install_headers import install_headers
from gi.repository import Gtk, Adw

from yumex.constants import rootdir


@Gtk.Template(resource_path=f"{rootdir}/ui/package_row.ui")
class YumexPackageRow(Adw.ActionRow):
    __gtype_name__ = "YumexPackageRow"

    installed = Gtk.Template.Child("installed")
    version = Gtk.Template.Child("version")
    repo = Gtk.Template.Child("repo")

    def __init__(self, name, desc, repo="fedora",version="1.0.0-23", installed=False, **kwargs):
        super().__init__(**kwargs)

        self.set_name(name)
        self.set_title(name)
        self.set_subtitle(desc)
        self.installed.set_visible(installed)
        if installed:
            # self.set_icon_name("user-trash-symbolic")
            self.add_css_class("accent")
        # else:
            # self.set_icon_name("system-software-install-symbolic")
        self.version.set_label(version)
        self.repo.set_label(repo)            
