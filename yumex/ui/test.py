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

from typing import List
from abc import abstractmethod


import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, GObject, Gio  # noqa: E402


class ViewColumnBase(Gtk.ColumnViewColumn):
    """ColumnViewColumn base class, it setup the basic factory, selection model & data model
    handlers must be overloaded & implemented in a sub class
    """

    def __init__(self, model_cls, col_view):
        Gtk.ColumnViewColumn.__init__(self)
        self.view = col_view
        # Use the signal Factory, so we can connect our own methods to setup
        self.factory = Gtk.SignalListItemFactory()
        # connect to Gtk.SignalListItemFactory signals
        # check https://docs.gtk.org/gtk4/class.SignalListItemFactory.html for details
        self.factory.connect("setup", self.factory_setup)
        self.factory.connect("bind", self.factory_bind)
        self.factory.connect("unbind", self.factory_unbind)
        self.factory.connect("teardown", self.factory_teardown)
        # Create data model, use our own class as elements
        self.set_factory(self.factory)
        self.store = self.setup_store(model_cls)
        # create a selection model containing our data model
        self.model = Gtk.SingleSelection.new(self.store)
        self.model.connect("selection-changed", self.on_selection_changed)
        # add model to the ColumnView
        self.view.set_model(self.model)

    @abstractmethod
    def setup_store(self, model_cls) -> Gio.ListModel:
        """Setup the data model
        can be overloaded in subclass to use another Gio.ListModel
        """
        return Gio.ListStore.new(model_cls)

    def add(self, elem):
        """add element to the data model"""
        self.store.append(elem)

    # Gtk.SignalListItemFactory signal callbacks
    # transfer to some some callback stubs, there can be overloaded in
    # a subclass.

    def on_selection_changed(self, widget, position, n_items):
        # get the current selection (GtkBitset)
        selection = widget.get_selection()
        # the the first value in the GtkBitset, that contain the index of
        # the selection in the data model
        # as we use Gtk.SingleSelection, there can only be one ;-)
        ndx = selection.get_nth(0)
        self.selection_changed(widget, ndx)

    # --------------------> abstract callback methods <--------------------------------
    # Implement these methods in your subclass

    @abstractmethod
    def factory_setup(self, widget: Gtk.ColumnViewColumn, item: Gtk.ListItem):
        """Setup the widgets to go into the ColumnViewColumn (Overload in subclass)"""
        pass

    @abstractmethod
    def factory_bind(self, widget: Gtk.ColumnViewColumn, item: Gtk.ListItem):
        """apply data from model to widgets set in setup (Overload in subclass)"""
        pass

    @abstractmethod
    def factory_unbind(self, widget: Gtk.ColumnViewColumn, item: Gtk.ListItem):
        pass

    @abstractmethod
    def factory_teardown(self, widget: Gtk.ColumnViewColumn, item: Gtk.ListItem):
        pass

    @abstractmethod
    def selection_changed(self, widget, ndx):
        """trigged when selecting in listview is changed
        ndx: is the index in the data store model that is selected
        """
        pass


class ColumnElem(GObject.GObject):
    """custom data element for a ColumnView model (Must be based on GObject)"""

    def __init__(self, name: str):
        super(ColumnElem, self).__init__()
        self.name = name

    def __repr__(self):
        return f"ColumnElem(name: {self.name})"


class MyColumnViewColumn(ViewColumnBase):
    """Custom ColumnViewColumn"""

    def __init__(
        self, win: Gtk.ApplicationWindow, col_view: Gtk.ColumnView, data: List
    ):
        # Init ListView with store model class.
        super(MyColumnViewColumn, self).__init__(ColumnElem, col_view)
        self.win = win
        # put some data into the model
        for elem in data:
            self.add(ColumnElem(elem))

    def factory_setup(self, widget, item: Gtk.ListItem):
        """Gtk.SignalListItemFactory::setup signal callback
        Handles the creation widgets to put in the ColumnViewColumn
        """
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        label.set_margin_start(10)
        item.set_child(label)

    def factory_bind(self, widget, item: Gtk.ListItem):
        """Gtk.SignalListItemFactory::bind signal callback
        Handles adding data for the model to the widgets created in setup
        """
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        label.set_text(data.name)  # Update Gtk.Label with data from model item


class Package(GObject.GObject):
    """custom data element for a ColumnView model (Must be based on GObject)"""

    def __init__(self, name: str, version: str, repo: str):
        super(Package, self).__init__()
        self.name = name
        self.version = version
        self.repo = repo

    def __repr__(self):
        return f"{self.name}-{self.version} from {self.repo}"


class PackageStore:
    store = Gio.ListStore.new(Package)

    def add_packages(self, data):
        for (name, version, repo) in data:
            self.store.append(Package(name, version, repo))


class PackageColumn(ViewColumnBase):
    """Custom ColumnViewColumn"""

    def __init__(self, view, title, attr_name):
        # Init ListView with store model class.
        ViewColumnBase.__init__(self, Package, view)
        self.attr_name = attr_name
        self.set_title(title)
        self.props.resizable = True

    def setup_store(self, model_cls) -> Gio.ListModel:
        """Setup the data model
        can be overloaded in subclass to use another Gio.ListModel
        """
        return self.view.store.store

    def factory_setup(self, widget, item: Gtk.ListItem):
        """Gtk.SignalListItemFactory::setup signal callback
        Handles the creation widgets to put in the ColumnViewColumn
        """
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        label.set_margin_start(10)
        item.set_child(label)

    def factory_bind(self, widget, item: Gtk.ListItem):
        """Gtk.SignalListItemFactory::bind signal callback
        Handles adding data for the model to the widgets created in setup
        """
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        label.set_text(
            getattr(data, self.attr_name)
        )  # Update Gtk.Label with data from model item


class YumexPackageView(Gtk.ColumnView):
    def __init__(self, window, **kwargs):
        Gtk.ColumnView.__init__(self, **kwargs)
        self.props.hexpand = True
        self.props.vexpand = True
        self.props.show_column_separators = True
        self.win = window
        self.store = PackageStore()
        data = [(f"package{nr}", f"{nr}.{nr}", "fedora") for nr in range(1, 10000)]
        self.store.add_packages(data)
        self.names = PackageColumn(self, "Name", "name")
        self.versions = PackageColumn(self, "Version", "version")
        self.repos = PackageColumn(self, "Repo", "repo")
        self.append_column(self.names)
        self.append_column(self.versions)
        self.append_column(self.repos)


def build_package_view(win):
    # ColumnView with custom columns
    columnview = YumexPackageView(win)
    return columnview


def build_view(win):
    # ColumnView with custom columns
    columnview = Gtk.ColumnView()
    columnview.set_show_column_separators(True)
    data = [f"Data Row: {row}" for row in range(5000)]
    for i in range(4):
        column = MyColumnViewColumn(win, columnview, data)
        column.set_title(f"Column {i}")
        columnview.append_column(column)
    lw_frame = Gtk.Frame()
    lw_frame.set_valign(Gtk.Align.FILL)
    lw_frame.set_vexpand(True)
    lw_frame.set_margin_start(20)
    lw_frame.set_margin_end(20)
    lw_frame.set_margin_top(10)
    lw_frame.set_margin_bottom(10)
    sw = Gtk.ScrolledWindow()
    sw.set_child(columnview)
    lw_frame.set_child(sw)
    return lw_frame
