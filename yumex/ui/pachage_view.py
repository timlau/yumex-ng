from gi.repository import Gtk, Gio, GObject

from yumex.constants import rootdir


class Package(GObject.GObject):
    """custom data element for a ColumnView model (Must be based on GObject)"""

    def __init__(self, name: str, version: str, repo: str):
        super(Package, self).__init__()
        self.name = name
        self.version = version
        self.repo = repo

    def __repr__(self):
        return f"{self.name}-{self.version} from {self.repo}"


@Gtk.Template(resource_path=f"{rootdir}/ui/package_view.ui")
class YumexPackageView(Gtk.ColumnView):
    __gtype_name__ = "YumexPackageView"

    names = Gtk.Template.Child("names")
    versions = Gtk.Template.Child("versions")
    repos = Gtk.Template.Child("repos")

    selection = Gtk.Template.Child("selection")

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.win = window
        self.store = Gio.ListStore.new(Package)
        self.selection.set_model(self.store)
        self.last_position = -1
        self.column_num = 0
        self.props.hexpand = True
        self.props.vexpand = True
        self.props.show_column_separators = True

    def add_packages(self, data):
        for (name, version, repo) in data:
            self.store.append(Package(name, version, repo))

    @Gtk.Template.Callback()
    def on_packages_setup(self, widget, item):
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        label.set_margin_start(10)
        item.set_child(label)

    @Gtk.Template.Callback()
    def on_name_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        label.set_text(data.name)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_version_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        label.set_text(data.version)  # Update Gtk.Label with data from model item

    @Gtk.Template.Callback()
    def on_repo_bind(self, widget, item):
        label = item.get_child()  # Get the Gtk.Label stored in the ListItem
        data = item.get_item()  # get the model item, connected to current ListItem
        label.set_text(data.repo)  # Update Gtk.Label with data from model item

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
