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


from dataclasses import dataclass, field


@dataclass
class TransactionResult:
    """transaction result object
    contains a state of the transaction and the the data
    or an error string is transaction failed
    """

    completed: bool
    data: dict = field(default_factory=dict)
    error: str = ""
    key_install: bool = False
    key_values: tuple = None
