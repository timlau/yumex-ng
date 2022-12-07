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

import logging


def setup_logging(debug=True):
    if debug:
        logging.basicConfig(
            level=logging.DEBUG, format="%(levelname)-6s: (%(name)-5s) -  %(message)s"
        )
    else:
        logging.basicConfig(
            level=logging.WARNING, format="%(levelname)-6s: (%(name)-5s) -  %(message)s"
        )


def log(txt):
    logger = logging.getLogger(name="yumex")
    logger.debug(txt)
