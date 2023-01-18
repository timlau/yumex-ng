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

import sys
import logging
import traceback
import threading
import time

from gi.repository import GLib


from yumex.constants import BUILD_TYPE

logger = logging.getLogger(name="yumex")


def setup_logging(debug=False):
    if BUILD_TYPE == "debug" or debug:
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
    """debug logging"""
    logger.debug(txt)


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
        log(f">> Running async job : {self.task_func.__name__}.")

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
            # traceback_info = "\n".join(traceback.format_tb(trace))
            # log([str(exception), traceback_info])
        self.source_id = GLib.idle_add(self.callback, result, error)
        log(f"<< Completed async job : {self.task_func.__name__}.")
        return self.source_id


class RunAsyncWait(threading.Thread):
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
        self.join()
        log("RunAsyncWait Done")

    def target(self, *args, **kwargs):
        result = None
        error = None
        log(f">> Running async wait job : {self.task_func.__name__}.")

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
            # traceback_info = "\n".join(traceback.format_tb(trace))
            # log([str(exception), traceback_info])
        self.source_id = GLib.idle_add(self.callback, result, error)
        log(f"<< Completed async wait job : {self.task_func.__name__}.")
        return self.source_id


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
        log(f">> starting {name} ({call_args})")
        t_start = time.perf_counter()
        rc = func(*args, **kwargs)
        t_end = time.perf_counter()
        log(f"<< {name} took {t_end - t_start:.4f} sec")
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
        log(f">> starting {name}")
        t_start = time.perf_counter()
        rc = func(*args, **kwargs)
        t_end = time.perf_counter()
        log(f"<< {name} took {t_end - t_start:.4f} sec")
        return rc

    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func
