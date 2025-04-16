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

from gi.repository import Adw, Gio, GLib, GObject, Gtk  # type: ignore

from yumex.constants import ROOTDIR
from yumex.utils import format_number


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/transaction_result.ui")
class YumexTransactionResult(Adw.Dialog):
    __gtype_name__ = "YumexTransactionResult"

    result_frame = Gtk.Template.Child()
    result_view = Gtk.Template.Child()
    selection = Gtk.Template.Child()
    result_factory = Gtk.Template.Child()
    prob_grp = Gtk.Template.Child()
    problems: Adw.ActionRow = Gtk.Template.Child()
    confirm_button = Gtk.Template.Child("confirm")
    cancel_button = Gtk.Template.Child("cancel")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._loop = GLib.MainLoop()
        self.confirm = False
        self.store = Gio.ListStore.new(ResultElem)
        model = Gtk.TreeListModel.new(self.store, False, True, self.add_tree_node)
        self.selection.set_model(model)

    def show(self, win):
        self.present(win)
        self._loop.run()

    def set_problems(self, prob: list):
        self.problems.set_subtitle("\n".join(prob))
        self.prob_grp.set_visible(True)

    def show_result(self, result_dict):
        self.set_follows_content_size(False)
        self.result_frame.set_visible(True)
        self.populate(result_dict)

    def show_errors(self, errors) -> None:
        self.result_frame.set_visible(False)
        self.confirm_button.set_visible(False)
        self.set_follows_content_size(True)
        self.problems.set_title(_("Transaction Failed"))
        self.problems.set_subtitle(errors)
        self.prob_grp.set_visible(True)

    def populate(self, result_dict):
        for key in result_dict:
            if key in ["replaced"]:
                continue
            childen = [ResultElem(result_elem=(name, repo, size)) for (name, repo), size in result_dict[key]]
            elem = ResultElem(title=self._get_title(key), children=childen)
            self.store.append(elem)

    def add_tree_node(self, item):
        if not item.children:
            return None
        store = Gio.ListStore.new(ResultElem)
        for child in item.children:
            store.append(child)
        return store

    def _get_title(self, action):
        match action:
            case "install":
                return _("Packages for installation")
            case "remove":
                return _("Packages for deletion")
            case "update":
                return _("Packages for updating")
            case "upgrade":
                return _("Packages for updating")
            case "skipped":
                return _("Skipped Packages")
            case "downgrade":
                return _("Packages for downgrading")
            case _:
                return action

    @Gtk.Template.Callback()
    def on_confirm_clicked(self, button):
        self._loop.quit()
        self.confirm = True
        self.close()

    @Gtk.Template.Callback()
    def on_cancel_clicked(self, button):
        self._loop.quit()
        self.close()

    @Gtk.Template.Callback()
    def on_setup(self, widget, item):
        """Setup the widget to show in the Gtk.Listview"""
        label = Gtk.Label()
        expander = Gtk.TreeExpander.new()
        expander.set_child(label)
        item.set_child(expander)

    @Gtk.Template.Callback()
    def on_bind(self, widget, item):
        """bind data from the store object to the widget"""
        expander = item.get_child()
        label = expander.get_child()
        row = item.get_item()
        expander.set_list_row(row)
        obj = row.get_item()
        if obj.title:
            label.set_label(obj.title)
        else:
            label.set_label(obj.pkg)


class ResultElem(GObject.GObject):
    def __init__(self, title=None, result_elem=None, children=None):
        super().__init__()
        self.title = title
        if result_elem:
            (pkg, repo, size) = result_elem
            self.pkg = pkg
            self.repo = repo
            self.size = format_number(size)
        else:
            self.pkg = ""
            self.repo = ""
            self.size = ""
        self.children = children
