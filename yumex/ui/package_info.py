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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yumex.ui.window import YumexMainWindow

from gi.repository import Gtk, Adw

from yumex.constants import ROOTDIR
import hawkey

from yumex.utils.enums import InfoType

ADVISORY_TYPES = {
    hawkey.ADVISORY_BUGFIX: _("Bugfix"),
    hawkey.ADVISORY_UNKNOWN: _("New Package"),
    hawkey.ADVISORY_SECURITY: _("Security"),
    hawkey.ADVISORY_ENHANCEMENT: _("Enhancement"),
}


@Gtk.Template(resource_path=f"{ROOTDIR}/ui/package_info.ui")
class YumexPackageInfo(Gtk.Box):
    __gtype_name__ = "YumexPackageInfo"

    release = Gtk.Template.Child()
    type = Gtk.Template.Child()
    issued = Gtk.Template.Child()
    info = Gtk.Template.Child()
    desc = Gtk.Template.Child()
    description_grp = Gtk.Template.Child()
    update_info_grp = Gtk.Template.Child()
    ref_grp = Gtk.Template.Child()
    references = Gtk.Template.Child()

    def __init__(self, win, **kwargs):
        super().__init__(**kwargs)
        self.win: YumexMainWindow = win
        self._ref_rows = []

    def clear(self):
        """clear the package info"""
        self.add_decription("")
        self.update_info_grp.set_visible(False)
        self.description_grp.set_visible(True)

    def update(self, info_type: InfoType, pkg_info):
        if pkg_info:
            info = self.format(info_type, pkg_info)
            match info_type:
                case InfoType.UPDATE_INFO:
                    if info:
                        self.add_update_info(info)
                        self.update_info_grp.set_visible(True)
                        self.description_grp.set_visible(False)
                    else:
                        self.add_decription(_("no update information found"))
                        self.update_info_grp.set_visible(False)
                        self.description_grp.set_visible(True)
                case _:
                    self.add_decription(info)
                    self.update_info_grp.set_visible(False)
                    self.description_grp.set_visible(True)
        else:
            self.clear()

    def format(self, info_type: InfoType, pkg_info):
        match info_type:
            case InfoType.DESCRIPTION:
                # a string
                return pkg_info
            case InfoType.FILES:
                # list of filename
                return "\n".join(pkg_info)
            case InfoType.UPDATE_INFO:
                # a list of update_info dicts
                if pkg_info:
                    return pkg_info[0]
                else:
                    return None

    def add_decription(self, txt):
        if not txt:
            txt = ""
        self.info.set_title(txt)

    def add_update_info(self, pkg_info):
        if pkg_info:
            release = pkg_info["id"]
            self.release.set_label(release)
            upd_type = ADVISORY_TYPES[pkg_info["type"]]
            self.type.set_label(upd_type)
            issued = pkg_info["updated"]
            self.issued.set_label(issued)
            description = pkg_info["description"]
            self.desc.set_title(description)
            refs = pkg_info["references"]
            # remove the previous added rows
            for row in self._ref_rows:
                self.ref_grp.remove(row)
            self._ref_rows = []
            if refs:
                for ref in refs:
                    num, bug_id, bug_desc, bug_link = ref
                    txt = f'<a href="{bug_link}">{bug_id}</a> - {bug_desc}'
                    row = Adw.ActionRow()
                    row.set_title(txt)
                    self.ref_grp.add(row)
                    self._ref_rows.append(row)
                self.references.set_visible(True)
            else:
                self.references.set_visible(False)
