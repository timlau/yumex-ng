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

from gi.repository import Gtk, Gio
from yumex.backend.interface import PackageCache

from yumex.constants import rootdir

from yumex.backend import YumexPackage
from yumex.ui import get_package_selection_tooltip
from yumex.ui.pachage_view import YumexPackageView
from yumex.utils import RunAsync, timed
from yumex.utils.enums import PackageState


@Gtk.Template(resource_path=f"{rootdir}/ui/queue_view.ui")
class YumexQueueView(Gtk.ListView):
    __gtype_name__ = "YumexQueueView"

    selection = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.win = window
        self.store = Gio.ListStore.new(YumexPackage)
        self.selection.set_model(self.store)

    def reset(self):
        self.store = Gio.ListStore.new(YumexPackage)
        self.selection.set_model(self.store)

    @property
    def cache(self) -> PackageCache:
        return self.win.package_view.package_cache

    @property
    def package_view(self) -> YumexPackageView:
        return self.win.package_view

    def contains(self, pkg):
        return pkg in self.store

    def add_package(self, pkg):
        self.add_packages([pkg])

    @timed
    def add_packages(self, pkgs):
        """Add package to queue"""

        def completed(deps, error=None):
            for dep in self.cache.add_packages(deps):
                if dep not in self.store:  # new dep not in queue
                    dep.queued = True
                    dep.is_dep = True
                    dep.ref_to = pkg
                    dep.queue_action = True
                self.store.insert_sorted(dep, self.sort_by_state)
            self.package_view.refresh()
            self.win.set_sensitive(True)

        for pkg in pkgs:
            if pkg not in self.store:
                self.store.insert_sorted(pkg, self.sort_by_state)
        self.win.set_sensitive(False)
        RunAsync(self.win.package_view.backend.depsolve, completed, self.store)

    def remove_package(self, pkg):
        self.remove_packages([pkg])

    @timed
    def remove_packages(self, pkgs):
        """Remove package from queue"""

        def completed(deps, error=None):
            for dep in self.cache.add_packages(deps):
                if dep not in store:  # new dep not in queue
                    dep.queued = True
                    dep.is_dep = True
                    dep.queue_action = True
                    store.insert_sorted(dep, self.sort_by_state)
            self.store = store
            self.selection.set_model(self.store)
            self.package_view.refresh()
            self.win.set_sensitive(True)

        store = Gio.ListStore.new(YumexPackage)
        for store_pkg in self.store:
            # check if this package should be kept in the queue
            if store_pkg not in pkgs and not store_pkg.is_dep:
                store.insert_sorted(store_pkg, self.sort_by_state)
            else:  # reset properties for pkg to not keep in queue
                store_pkg.queued = False
                store_pkg.is_dep = False
                store_pkg.queue_action = True
        if len(store):  # check if there something in the queue
            self.win.set_sensitive(False)
            RunAsync(self.win.package_view.backend.depsolve, completed, store)
        else:
            completed([])

    def clear_all(self):
        self.remove_packages(self.store)

    def get_queued(self) -> list[YumexPackage]:
        return [pkg for pkg in self.store if not pkg.is_dep]

    @staticmethod
    def sort_by_state(a, b):
        return (a.state + a.action) > (b.state + b.action)

    def find_by_nevra(self, nevra):
        for pkg in self.store:
            if pkg.nevra == nevra:
                return pkg
        return None

    @Gtk.Template.Callback()
    def on_queue_setup(self, widget, item):
        """setup ui for a list item"""
        row = YumexQueueRow(self)
        item.set_child(row)
        item.set_activatable(False)

    @Gtk.Template.Callback()
    def on_queue_bind(self, widget, item):
        """setup data for a list item"""
        row = item.get_child()
        pkg = item.get_item()
        row.text.set_label(pkg.nevra)
        row.pkg = pkg
        row.dep.set_visible(pkg.is_dep)
        # set pkg label tooltip bases on pkg state
        tip = get_package_selection_tooltip(pkg)
        row.text.set_tooltip_text(tip)
        row.icon.set_tooltip_text(tip)
        row.dep.set_tooltip_text(tip)
        match pkg.state:
            case PackageState.INSTALLED:
                row.icon.set_from_icon_name("edit-delete-symbolic")
                row.icon.add_css_class("error")
            case PackageState.AVAILABLE:
                row.icon.set_from_icon_name("emblem-default-symbolic")
                row.icon.add_css_class("success")
            case PackageState.UPDATE:
                row.icon.set_from_icon_name("emblem-synchronizing-symbolic")
                row.icon.add_css_class("accent")


@Gtk.Template(resource_path=f"{rootdir}/ui/queue_row.ui")
class YumexQueueRow(Gtk.Box):
    __gtype_name__ = "YumexQueueRow"

    icon = Gtk.Template.Child()
    text = Gtk.Template.Child()
    dep = Gtk.Template.Child()

    def __init__(self, view, **kwargs):
        super().__init__(**kwargs)
        self.view: YumexQueueView = view
        self.pkg: YumexPackage = None

    @Gtk.Template.Callback()
    def on_delete_clicked(self, button):
        """row delete button cliecked"""
        # row -> box -> box -> button
        row = button.get_parent()
        pkg = row.pkg
        if pkg:
            row.view.remove_package(pkg)
            pkg.queued = False
