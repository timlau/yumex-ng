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

from yumex.utils.enums import PackageTodo


def get_package_selection_tooltip(pkg):
    """set tooltip based on package state and if it is an denpency"""
    tip = ""
    name = ""
    if not pkg:
        return ""
    if pkg.is_dep:
        if pkg.ref_to:
            name = f" ({str(pkg.ref_to.nevra)})"
        match pkg.todo:
            case PackageTodo.REMOVE:
                tip = _(f"Queued for deletion as a dependency {name}")
            case PackageTodo.INSTALL:
                tip = _(f"Queued for installation as a dependency {name}")
            case PackageTodo.UPDATE:
                tip = _(f"Queued for updating as a dependency {name}")
            case PackageTodo.REINSTALL:
                tip = _(f"Queued for reinstallation as a dependency {name}")
            case PackageTodo.DOWNGRADE:
                tip = _(f"Queued for downgrading as a dependency {name}")
            case PackageTodo.DISTROSYNC:
                tip = _(f"Queued for distribution synchronization as a dependency {name}")
    else:
        match pkg.todo:
            case PackageTodo.REMOVE:
                tip = _("Queued for deletion")
            case PackageTodo.INSTALL:
                tip = _("Queued for installation")
            case PackageTodo.UPDATE:
                tip = _("Queued for updating")
            case PackageTodo.REINSTALL:
                tip = _("Queued for reinstallation")
            case PackageTodo.DOWNGRADE:
                tip = _("Queued for downgrading")
            case PackageTodo.DISTROSYNC:
                tip = _("Queued for distribution synchronization")

    return tip


UPDATE_INFO_TEMPLATE = """Release: {}   Type: {}   Issued: {}

Description:
{}
"""
