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

from gi.repository import Gtk, Gio

from yumex.constants import rootdir

from yumex.backend import YumexPackage
from yumex.utils import log
from yumex.backend import PackageState


@Gtk.Template(resource_path=f"{rootdir}/ui/queue_view.ui")
class YumexQueueView(Gtk.ListView):
    __gtype_name__ = "YumexQueueView"

    selection = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.win = window
        self.store = Gio.ListStore.new(YumexPackage)
        self.selection.set_model(self.store)

    def add(self, pkg):
        """Add package to queue"""
        if pkg not in self.store:
            self.store.insert_sorted(pkg, lambda a, b: a.state > b.state)

    def remove(self, pkg):
        """Remove package from queue"""
        if pkg in self.store:
            found, ndx = self.store.find(pkg)
            if found:
                self.store.remove(ndx)
            else:
                log(f"{pkg} was not found in queue")

    @Gtk.Template.Callback()
    def on_queue_setup(self, widget, item):
        """setup ui for a list item"""
        row = YumexQueueRow(self)
        item.set_child(row)

    @Gtk.Template.Callback()
    def on_queue_bind(self, widget, item):
        """setup data for a list item"""
        row = item.get_child()
        data = item.get_item()
        row.text.set_label(data.nevra)
        row.pkg = data
        match data.state:
            case PackageState.INSTALLED:
                row.icon.set_from_icon_name("edit-delete-symbolic")
                row.icon.set_tooltip_text(_("Package will be deleted"))
                row.icon.add_css_class("error")
            case PackageState.AVAILABLE:
                row.icon.set_from_icon_name("emblem-default-symbolic")
                row.icon.set_tooltip_text(_("Package will be installed"))
                row.icon.add_css_class("success")
            case PackageState.UPDATE:
                row.icon.set_from_icon_name("emblem-synchronizing-symbolic")
                row.icon.set_tooltip_text(_("Package will be updated"))
                row.icon.add_css_class("accent")


@Gtk.Template(resource_path=f"{rootdir}/ui/queue_row.ui")
class YumexQueueRow(Gtk.Box):
    __gtype_name__ = "YumexQueueRow"

    icon = Gtk.Template.Child()
    text = Gtk.Template.Child()

    def __init__(self, view, **kwargs):
        super().__init__(**kwargs)
        self.view = view
        self.pkg = None

    @Gtk.Template.Callback()
    def on_delete_clicked(self, button):
        """row delete button cliecked"""
        # row -> box -> box -> button
        row = button.get_parent().get_parent().get_parent()
        pkg = row.pkg
        if pkg:
            row.view.remove(pkg)
            pkg.queued = False
