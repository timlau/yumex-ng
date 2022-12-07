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
#
# Copyright (C) 2022  Tim Lauridsen
#
#

import time

from gi.repository import Gtk, Gio

from yumex.constants import rootdir
from yumex.backend import YumexPackage
from yumex.backend.dnf import Backend
from yumex.utils import log

CLEAN_STYLES = ["success", "error", "accent", "warning"]


@Gtk.Template(resource_path=f"{rootdir}/ui/package_view.ui")
class YumexPackageView(Gtk.ColumnView):
    __gtype_name__ = "YumexPackageView"

    names = Gtk.Template.Child("names")
    versions = Gtk.Template.Child("versions")
    repos = Gtk.Template.Child("repos")
    queued = Gtk.Template.Child()
    archs = Gtk.Template.Child()
    sizes = Gtk.Template.Child()
    descriptions = Gtk.Template.Child()

    selection = Gtk.Template.Child("selection")

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.win = window
        self.store = Gio.ListStore.new(YumexPackage)
        self.selection.set_model(self.store)
        self.last_position = -1
        self.column_num = 0
        self.backend = Backend()

    def get_packages(self, pkg_filter="available"):
        log("Loading packages")
        st = time.time()
        pkgs = sorted(
            self.backend.get_packages(pkg_filter), key=lambda n: n.name.lower()
        )
        et = time.time()
        elapsed = time.strftime("%H:%M:%S", time.gmtime(et - st))
        log(f"Execution time: {elapsed}")
        self.add_packages_to_store(pkgs)

    def search(self, txt):
        if len(txt) > 2:
            log("search packages")
            pkgs = self.backend.search(txt)
            self.add_packages_to_store(pkgs)

    def add_packages_to_store(self, pkgs):
        log("Adding packages to store")
        st = time.time()
        # create a new store and add packages (big speed improvement)
        store = Gio.ListStore.new(YumexPackage)
        for pkg in sorted(pkgs, key=lambda n: n.name.lower()):
            store.append(pkg)
        self.store = store
        self.selection.set_model(self.store)
        et = time.time()
        log(f"number of packages : {len(pkgs)}")
        elapsed = time.strftime("%H:%M:%S", time.gmtime(et - st))
        log(f"Execution time: {elapsed}")

    def set_styles(self, item, data):
        current_styles = item.get_css_classes()
        current_styles = [
            style for style in current_styles if style not in CLEAN_STYLES
        ]
        current_styles += data.styles
        item.set_css_classes(current_styles)

    @Gtk.Template.Callback()
    def on_package_column_checkmark_setup(self, widget, item):
        check = Gtk.CheckButton()
        check.connect("toggled", self.on_queued_toggled, item)
        item.set_child(check)

    @Gtk.Template.Callback()
    def on_package_column_text_setup(self, widget, item):
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        label.set_margin_start(10)
        item.set_child(label)

    @Gtk.Template.Callback()
    def on_name_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, data)
        label.set_text(data.name)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_version_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, data)
        label.set_text(data.evr)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_repo_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, data)
        label.set_text(data.repo)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_arch_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, data)
        label.set_text(data.arch)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_size_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, data)
        label.set_text(data.size)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_description_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        self.set_styles(label, data)
        label.set_text(data.description)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_queued_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        label.set_active(data.queued)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_selection_changed(self, widget, position, n_items):
        pass
        # get the current selection (GtkBitset)
        # selection = widget.get_selection()
        # # the first value contain the index of the selection in the data model
        # # as we use Gtk.SingleSelection, there can only be one ;-)
        # ndx = selection.get_nth(0)
        # msg = f"Row {ndx} was selected ( {self.store[ndx]} )"
        # self.win.show_message(msg)

    def on_queued_toggled(self, widget, item):
        """update the dataobject with the current check state"""
        data = item.get_item()
        data.queued = widget.get_active()
