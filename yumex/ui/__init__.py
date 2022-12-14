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

from yumex.backend import PackageState


def get_package_selection_tooltip(pkg):
    """set tooltip based on package state and if it is an denpency"""
    tip = ""
    if pkg.is_dep:
        match pkg.state:
            case PackageState.INSTALLED:
                tip = _("Queued for deletion as a dependency")
            case PackageState.AVAILABLE:
                tip = _("Queued for installation as a dependency")
            case PackageState.UPDATE:
                tip = _("Queued for updating as a dependency")
    else:
        match pkg.state:
            case PackageState.INSTALLED:
                tip = _("Queued for deletion")
            case PackageState.AVAILABLE:
                tip = _("Queued for installation")
            case PackageState.UPDATE:
                tip = _("Queued for updating")

    return tip
