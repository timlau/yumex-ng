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

import sys
import logging
import traceback
import threading

from gi.repository import GLib


from yumex.constants import build_type


def setup_logging():
    if build_type == "debug":
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        logging.basicConfig(
            level=logging.WARNING,
            format="%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s",
            datefmt="%H:%M:%S",
        )


def log(txt):
    logger = logging.getLogger(name="yumex")
    logger.debug(txt)


class RunAsync(threading.Thread):
    def __init__(self, task_func, callback, *args, **kwargs):
        self.source_id = None
        if threading.current_thread() is not threading.main_thread():
            raise AssertionError

        super(RunAsync, self).__init__(target=self.target, args=args, kwargs=kwargs)

        self.task_func = task_func

        self.callback = callback if callback else lambda r, e: None
        self.daemon = kwargs.pop("daemon", True)

        self.start()

    def target(self, *args, **kwargs):
        result = None
        error = None

        log(f"Running async job [{self.task_func}].")

        try:
            result = self.task_func(*args, **kwargs)
        except Exception as exception:
            log(
                "Error while running async job: "
                f"{self.task_func}\nException: {exception}"
            )

            error = exception
            _ex_type, _ex_value, trace = sys.exc_info()
            traceback.print_tb(trace)
            traceback_info = "\n".join(traceback.format_tb(trace))

            log([str(exception), traceback_info])
        self.source_id = GLib.idle_add(self.callback, result, error)
        return self.source_id
