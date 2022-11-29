from distutils.command.install_headers import install_headers
from gi.repository import Gtk, Adw

from yumex.constants import rootdir


@Gtk.Template(resource_path=f"{rootdir}/ui/package_row.ui")
class YumexPackageRow(Adw.ActionRow):
    __gtype_name__ = "YumexPackageRow"

    installed = Gtk.Template.Child("installed")
    version = Gtk.Template.Child("version")
    repo = Gtk.Template.Child("repo")
    install_button = Gtk.Template.Child("install-button")
    remove_button = Gtk.Template.Child("remove-button")

    def __init__(self, name, desc, repo="fedora",version="1.0.0-23", installed=False, **kwargs):
        super().__init__(**kwargs)

        self.set_name(name)
        self.set_title(name)
        self.set_subtitle(desc)
        self.installed.set_visible(installed)
        if installed:
            self.install_button.set_visible(False)
            self.add_css_class("accent")
        else:
            self.remove_button.set_visible(False)
        self.version.set_label(version)
        self.repo.set_label(repo)            
