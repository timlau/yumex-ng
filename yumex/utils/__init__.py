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
# Copyright (C) 2025 Tim Lauridsen

import logging
import logging.handlers
import re
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import dbus
from gi.repository import GLib

from yumex.constants import BUILD_TYPE
from yumex.utils.exceptions import YumexException

logger = logging.getLogger(__name__)


def get_distro_release():
    find_rel = re.compile(r".*(\d\d).*")
    rel_file = Path("/etc/redhat-release")
    content = rel_file.read_text()
    release = find_rel.findall(content)[0]
    return release


def setup_logging(debug=False):
    if BUILD_TYPE == "debug" or debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s",
            datefmt="%H:%M:%S",
        )
        log_file = Path("~/.local/share/yumex/yumex_debug.log").expanduser()
        log_file.parent.mkdir(exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(log_file, backupCount=5)
        if log_file.exists():
            file_handler.doRollover()
        filte_formatter = logging.Formatter(
            "%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s", datefmt="%H:%M:%S"
        )
        file_handler.setFormatter(filte_formatter)
        logging.getLogger(name="yumex").addHandler(file_handler)
    else:
        logging.basicConfig(
            level=logging.WARNING,
            format="%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s",
            datefmt="%H:%M:%S",
        )


class RunAsync(threading.Thread):
    def __init__(self, task_func, callback, *args, **kwargs):
        self.source_id = None
        if threading.current_thread() is not threading.main_thread():
            raise AssertionError

        super().__init__(target=self.target, args=args, kwargs=kwargs)

        self.task_func = task_func

        self.callback = callback or (lambda r, e: None)
        # self.daemon = kwargs.pop("daemon", True)
        self.daemon = False
        self.start()

    def target(self, *args, **kwargs):
        result = None
        error = None
        logger.debug(f">> Running async job : {self.task_func.__name__}.")

        try:
            result = self.task_func(*args, **kwargs)
        except Exception as exception:
            logger.debug(f"Error while running async job: {self.task_func}\nException: {exception}")

            error = exception
            _ex_type, _ex_value, trace = sys.exc_info()
            traceback.print_tb(trace)
            # traceback_info = "\n".join(traceback.format_tb(trace))
            # log([str(exception), traceback_info])
        self.source_id = GLib.idle_add(self.callback, result, error)
        logger.debug(f"<< Completed async job : {self.task_func.__name__}.")
        return self.source_id


@dataclass
class JobResult:
    result: Any
    error: Any


class RunJob(threading.Thread):
    """Run a task in a thread and wait for it to complete using a GLib.Mainloop
    So the GUI don't get stalled with the task is running
    """

    def __init__(self, task_func: Callable, *args, **kwargs):
        self.result = None
        self._loop = GLib.MainLoop()
        if threading.current_thread() is not threading.main_thread():
            raise AssertionError
        super().__init__(target=self.target, args=args, kwargs=kwargs)
        self.task_func = task_func

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        logger.debug(f"<< Completed job : {self.task_func.__name__}.")
        if self._loop.is_running():
            self._loop.quit()

    def start(self):
        logger.debug(f">> Running job : {self.task_func.__name__}.")
        super().start()
        self._loop.run()
        return self.result

    def target(self, *args, **kwargs):
        result = self.task_func(*args, **kwargs)
        self.result = result
        self._loop.quit()


def format_number(number, SI=0, space=" "):
    """Turn numbers into human-readable metric-like numbers"""
    symbols = [
        "",  # (none)
        "K",  # kilo
        "M",  # mega
        "G",  # giga
        "T",  # tera
        "P",  # peta
        "E",  # exa
        "Z",  # zetta
        "Y",
    ]  # yotta

    step = 1000.0 if SI else 1024.0
    thresh = 999
    depth = 0
    max_depth = len(symbols) - 1

    # we want numbers between 0 and thresh, but don't exceed the length
    # of our list.  In that event, the formatting will be screwed up,
    # but it'll still show the right number.
    while number > thresh and depth < max_depth:
        depth += 1
        number = number / step

    if isinstance(number, int):
        # it's an int or a long, which means it didn't get divided,
        # which means it's already short enough
        fmt = "%i%s%s"
    elif number < 9.95:
        # must use 9.95 for proper sizing.  For example, 9.99 will be
        # rounded to 10.0 with the .1f fmt string (which is too long)
        fmt = "%.1f%s%s"
    else:
        fmt = "%.0f%s%s"

    return fmt % (float(number or 0), space, symbols[depth])


def timed_parms(func):
    """
    This decorator show the execution time of a function in the log
    """

    def new_func(*args, **kwargs):
        name = func.__name__
        call_args = repr(args[1:])
        logger.debug(f">> starting {name} ({call_args})")
        t_start = time.perf_counter()
        rc = func(*args, **kwargs)
        t_end = time.perf_counter()
        logger.debug(f"<< {name} took {t_end - t_start:.4f} sec")
        return rc

    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


def timed(func):
    """
    This decorator show the execution time of a function in the log
    """

    def new_func(*args, **kwargs):
        name = func.__name__
        logger.debug(f">> starting {name}")
        t_start = time.perf_counter()
        rc = func(*args, **kwargs)
        t_end = time.perf_counter()
        logger.debug(f"<< {name} took {t_end - t_start:.4f} sec")
        return rc

    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


def dbus_exception(func):
    """
    This decorator capture an dbus exception and raises a YumexException with the message
    """

    def new_func(*args, **kwargs):
        try:
            rc = func(*args, **kwargs)
            return rc
        except dbus.exceptions.DBusException as e:
            raise YumexException(str(e))

    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func
