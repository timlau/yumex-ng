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

from yumex.utils.enums import PackageState


def get_package_selection_tooltip(pkg):
    """set tooltip based on package state and if it is an denpency"""
    tip = ""
    name = ""
    if pkg.is_dep:
        if pkg.ref_to:
            name = f" ({str(pkg.ref_to.nevra)})"
        match pkg.state:
            case PackageState.INSTALLED:
                tip = _(f"Queued for deletion as a dependency {name}")
            case PackageState.AVAILABLE:
                tip = _(f"Queued for installation as a dependency {name}")
            case PackageState.UPDATE:
                tip = _(f"Queued for updating as a dependency {name}")
    else:
        match pkg.state:
            case PackageState.INSTALLED:
                tip = _("Queued for deletion")
            case PackageState.AVAILABLE:
                tip = _("Queued for installation")
            case PackageState.UPDATE:
                tip = _("Queued for updating")

    return tip


UPDATE_INFO_TEMPLATE = """Release: {}   Type: {}   Issued: {}

Description:
{}
"""
