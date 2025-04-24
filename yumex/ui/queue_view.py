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
# Copyright (C) 2024 Tim Lauridsen

import logging

from gi.repository import GObject, Gtk

from yumex.backend.dnf import YumexPackage
from yumex.constants import ROOTDIR
from yumex.ui import get_package_selection_tooltip
from yumex.utils import RunAsync
from yumex.utils.enums import PackageState, PackageTodo, Page
from yumex.utils.storage import PackageStorage

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/queue_view.ui")
class YumexQueueView(Gtk.ListView):
    __gtype_name__ = "YumexQueueView"
    __gsignals__ = {"refresh": (GObject.SignalFlags.RUN_FIRST, None, ())}

    selection = Gtk.Template.Child()

    def __init__(self, presenter, **kwargs):
        super().__init__(**kwargs)
        self.presenter = presenter
        self.storage = PackageStorage()
        self.selection.set_model(self.storage.get_storage())

    def reset(self):
        self.selection.set_model(self.storage.clear())
        self.refresh_attention()

    def refresh_attention(self):
        self.presenter.set_needs_attention(Page.QUEUE, len(self.storage))

    def contains(self, pkg):
        return pkg in self.storage

    def add_package(self, pkg):
        self.add_packages([pkg])

    def add_packages(self, pkgs):
        """Add package to queue"""
        logger.debug(f"QueueView.add_packages: {len(pkgs)}")
        for pkg in pkgs:
            if pkg not in self.storage:
                pkg.queue_action = True
                pkg.todo = self.get_todo(pkg)
                pkg.is_dep = False
                pkg.queued = True
                pkg.queue_action = False
                self.storage.insert_sorted(pkg, self.sort_by_state)
        RunAsync(self.presenter.depsolve, self.add_deps_to_queue, self.storage)

    def remove_package(self, pkg):
        self.remove_packages([pkg])

    def remove_packages(self, pkgs):
        """Remove package from queue"""
        logger.debug(f"QueueView.remove_packages: {len(pkgs)}")
        to_keep = []
        for store_pkg in self.storage:
            # check if this package should be kept in the queue
            if store_pkg not in pkgs and not store_pkg.is_dep:
                to_keep.append(store_pkg)
            else:  # reset properties for pkg to not keep in queue
                store_pkg.queue_action = True
                store_pkg.todo = PackageTodo.NONE
                store_pkg.queued = False
                store_pkg.is_dep = False
                store_pkg.queue_action = False
        store = self.storage.clear()
        if len(to_keep):  # check if there something in the queue
            for pkg in to_keep:
                self.storage.insert_sorted(pkg, self.sort_by_state)
            RunAsync(self.presenter.depsolve, self.add_deps_to_queue, store)
        else:
            self.add_deps_to_queue([])

    def add_deps_to_queue(self, deps, error=None):
        if deps is None:
            logger.debug("QueueView.add_deps_to_queue: deps = None")
            return
        logger.debug(f"QueueView.add_deps_to_queue: deps found : {len(deps)}")
        for dep in self.presenter.get_packages(deps):
            if dep not in self.storage:  # new dep not in queue
                dep.is_dep = True
                dep.queue_action = True
                dep.queued = True
                dep.todo = self.get_todo(dep)
                self.storage.insert_sorted(dep, self.sort_by_state)
        self.selection.set_model(self.storage.get_storage())
        # send refresh signal, to refresh the package view
        self.emit("refresh")
        self.refresh_attention()

    def clear_all(self):
        self.remove_packages(list(self.storage))

    def get_queued(self) -> list[YumexPackage]:
        return [pkg for pkg in self.storage if not pkg.is_dep]

    @staticmethod
    def sort_by_state(a, b):
        return (a.state + a.action) > (b.state + b.action)

    def find_by_nevra(self, nevra):
        return self.storage.find_by_nevra(nevra)

    def get_todo(self, pkg: YumexPackage) -> PackageTodo:
        """get todo action"""

        logger.debug(f"get_todo: todo: {pkg.todo} state: {pkg.state} for {pkg}")
        if pkg.todo != PackageTodo.NONE:
            return pkg.todo
        match pkg.state:
            case PackageState.INSTALLED:
                return PackageTodo.REMOVE
            case PackageState.AVAILABLE:
                return PackageTodo.INSTALL
            case PackageState.UPDATE:
                return PackageTodo.UPDATE
            case PackageState.DOWNGRADE:
                return PackageTodo.DOWNGRADE
            case state:
                logger.debug(f"get_todo: unknown state {state} for {pkg}")
        return PackageTodo.NONE

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
        row.set_tooltip()
        row.set_icon()


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/queue_row.ui")
class YumexQueueRow(Gtk.Box):
    __gtype_name__ = "YumexQueueRow"

    icon = Gtk.Template.Child()
    text = Gtk.Template.Child()
    dep = Gtk.Template.Child()

    def __init__(self, view, **kwargs):
        super().__init__(**kwargs)
        self.view: YumexQueueView = view
        self.pkg: YumexPackage = None

    def set_tooltip(self):
        tip = get_package_selection_tooltip(self.pkg)
        self.text.set_tooltip_text(tip)
        self.icon.set_tooltip_text(tip)
        self.dep.set_tooltip_text(tip)

    def set_icon(self):
        match self.pkg.todo:
            case PackageTodo.REMOVE:
                self.icon.set_from_icon_name("value-decrease-symbolic")
                self.icon.add_css_class("error")
            case PackageTodo.INSTALL:
                self.icon.set_from_icon_name("value-increase-symbolic")
                self.icon.add_css_class("success")
            case PackageTodo.UPDATE:
                self.icon.set_from_icon_name("starred-symbolic")
                self.icon.add_css_class("accent")
            case PackageTodo.DOWNGRADE:
                self.icon.set_from_icon_name("object-rotate-right-symbolic")
                self.icon.add_css_class("accent")
            case PackageTodo.REINSTALL:
                self.icon.set_from_icon_name("media-playlist-repeat-symbolic")
                self.icon.add_css_class("success")
            case PackageTodo.DISTROSYNC:
                self.icon.set_from_icon_name("object-rotate-left-symbolic")
                self.icon.add_css_class("accent")
            case state:
                logger.debug(f"set_icon: unknown state {state} for {self.pkg} todo {self.pkg.todo}")
                self.icon.set_from_icon_name("org.gnome.Settings-privacy-symbolic")
                self.icon.add_css_class("error")

    @Gtk.Template.Callback()
    def on_delete_clicked(self, button):
        """row delete button cliecked"""
        # row -> box -> box -> button
        row = button.get_parent()
        if pkg := row.pkg:
            row.view.remove_package(pkg)
            pkg.queued = False
