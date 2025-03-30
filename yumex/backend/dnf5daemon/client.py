# from gi.repository import GLib  # type: ignore
import logging
from functools import partial
from typing import Any, Self

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

DBusGMainLoop(set_as_default=True)

DNFDAEMON_BUS_NAME = "org.rpm.dnf.v0"
DNFDAEMON_OBJECT_PATH = "/" + DNFDAEMON_BUS_NAME.replace(".", "/")

IFACE_SESSION_MANAGER = "{}.SessionManager".format(DNFDAEMON_BUS_NAME)
IFACE_REPO = "{}.rpm.Repo".format(DNFDAEMON_BUS_NAME)
IFACE_RPM = "{}.rpm.Rpm".format(DNFDAEMON_BUS_NAME)
IFACE_GOAL = "{}.Goal".format(DNFDAEMON_BUS_NAME)
IFACE_BASE = "{}.Base".format(DNFDAEMON_BUS_NAME)
IFACE_GROUP = "{}.comps.Group".format(DNFDAEMON_BUS_NAME)
IFACE_ADVISORY = "{}.Advisory".format(DNFDAEMON_BUS_NAME)

logger = logging.getLogger(__name__)


# async call handler class
class AsyncCaller:
    def __init__(self) -> None:
        self.res = None
        self.err = None
        self.loop = None

    def error_handler(self, e) -> None:
        self.err = e
        self.loop.quit()

    def reply_handler(self, *args) -> None:
        if len(args) > 1:
            self.res = (value for value in args)
        else:
            self.res = args[0]
        self.loop.quit()

    def call(self, mth, *args, **kwargs) -> None | Any:
        self.loop = GLib.MainLoop()
        mth(
            *args,
            **kwargs,
            reply_handler=self.reply_handler,
            error_handler=self.error_handler,
        )
        self.loop.run()
        return self.res, self.err


class Dnf5DbusClient:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.iface_session = dbus.Interface(
            self.bus.get_object(DNFDAEMON_BUS_NAME, DNFDAEMON_OBJECT_PATH),
            dbus_interface=IFACE_SESSION_MANAGER,
        )
        self.async_dbus = AsyncCaller()
        self._connected = False

    def __enter__(self) -> Self:
        """context manager enter, return current object"""
        # get a session path for the dnf5daemon
        self.open_session()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """context manager exit"""
        self.close_session()
        if exc_type:
            logger.critical("", exc_info=(exc_type, exc_value, exc_traceback))
        # close dnf5 session

    def open_session(self):
        if not self._connected:
            self.session = self.iface_session.open_session({})
            logger.debug(f"open session: {self.session}")
            self._connected = True
            self.session_repo = dbus.Interface(
                self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
                dbus_interface=IFACE_REPO,
            )
            self.session_rpm = dbus.Interface(
                self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
                dbus_interface=IFACE_RPM,
            )
            self.session_goal = dbus.Interface(
                self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
                dbus_interface=IFACE_GOAL,
            )
            self.session_base = dbus.Interface(
                self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
                dbus_interface=IFACE_BASE,
            )
            self.session_advisory = dbus.Interface(
                self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
                dbus_interface=IFACE_ADVISORY,
            )
            self.session_group = dbus.Interface(
                self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
                dbus_interface=IFACE_GROUP,
            )

    def close_session(self):
        if self._connected:
            logger.debug(f"close session: {self.session}")
            self.iface_session.close_session(self.session)
            self._connected = False

    def _async_method(self, method: str, proxy=None) -> partial:
        """create a patial func to make an async call to a given
        dbus method name
        """
        return partial(self.async_dbus.call, getattr(proxy, method))

    def resolve(self, *args):
        resolve = self._async_method("resolve", proxy=self.session_goal)
        res, err = resolve(dbus.Array())
        if err:
            logger.error(err)
        return res, err

    def do_transaction(self):
        do_transaction = self._async_method("do_transaction", proxy=self.session_goal)
        options = {"comment": "Yum Extender Transaction"}
        res, err = do_transaction(options)
        if err:
            logger.error(err)
        return res

    def confirm_key(self, *args):
        return self.session_repo.confirm_key(args)

    def repo_list(self):
        get_list = self._async_method("list", proxy=self.session_repo)
        res, err = get_list({"repo_attrs": dbus.Array(["name", "enabled"])})
        if err:
            logger.error(err)
        return res

    def package_list(self, *args, **kwargs) -> list[list[str]]:
        """call the org.rpm.dnf.v0.rpm.Repo list method

        *args is package patterns to match
        **kwargs can contain other options like package_attrs, repo or scope

        """
        # logger.debug(f"\n --> args: {args} kwargs: {kwargs}")
        options = {}
        options["patterns"] = dbus.Array(args)
        options["package_attrs"] = dbus.Array(kwargs.pop("package_attrs", ["nevra"]))
        options["with_src"] = False
        # options["with_nevra"] = kwargs.pop("with_nevra", True)
        # options["with_provides"] = kwargs.pop("with_provides", False)
        # options["with_filenames"] = kwargs.pop("with_filenames", False)
        # options["with_binaries"] = kwargs.pop("with_binaries", False)
        options["icase"] = True
        options["latest-limit"] = 1
        # limit packages to one of “all”, “installed”, “available”, “upgrades”, “upgradable”
        options["scope"] = kwargs.pop("scope", "all")
        if "repo" in kwargs:
            options["repo"] = kwargs.pop("repo")
        if "arch" in kwargs:
            options["arch"] = kwargs.pop("arch")
        # get and async partial function
        # logger.debug(f" --> options: {options} ")
        get_list = self._async_method("list", proxy=self.session_rpm)
        res, err = get_list(options)
        # print(res, err)
        # return as native types.
        if err:
            logger.error(err)
        return res

    def advisory_list(self, *args, **kwargs):
        # logger.debug(f"\n --> args: {args} kwargs: {kwargs}")
        options = {}
        options["advisory_attrs"] = dbus.Array(kwargs.pop("advisor_attrs"))
        options["contains_pkgs"] = dbus.Array(args)
        options["availability"] = "all"
        # options[""] = get_variant(list[str], [])
        # logger.debug(f" --> options: {options} ")
        get_list = self._async_method("list", proxy=self.session_advisory)
        res, err = get_list(options)
        return res
