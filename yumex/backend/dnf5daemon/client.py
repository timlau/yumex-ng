import json
import logging
import os
import select
from functools import partial
from typing import Any

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib  # type: ignore

from yumex.utils import dbus_exception
from yumex.utils.exceptions import YumexException

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
IFACE_OFFLINE = "{}.Offline".format(DNFDAEMON_BUS_NAME)

logger = logging.getLogger(__name__)


# async call handler class
class AsyncCaller:
    def __init__(self) -> None:
        self.res = None
        self.err = None
        self.loop = None

    def error_handler(self, e) -> None:
        logger.error(e)
        self.err = e
        self.loop.quit()

    def reply_handler(self, *args) -> None:
        if len(args) > 1:
            self.res = args
        else:
            if args:
                self.res = args[0]
        self.loop.quit()

    def call(self, mth, *args, **kwargs) -> None | Any:
        self.loop = GLib.MainLoop()
        self.res = None
        self.err = None
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

    @dbus_exception
    def open_session(self, options={}):
        if not self._connected:
            logger.debug(f"DBUS: {self.iface_session.object_path}.open_session({options})")
            self.session = self.iface_session.open_session(options)
            if self.session:
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
                self.session_offline = dbus.Interface(
                    self.bus.get_object(DNFDAEMON_BUS_NAME, self.session),
                    dbus_interface=IFACE_OFFLINE,
                )
            else:
                raise YumexException("Couldn't open session to Dnf5Dbus")

    @dbus_exception
    def close_session(self):
        if self._connected:
            logger.debug(f"DBUS: {self.iface_session.object_path}.close_session()")
            rc = self.iface_session.close_session(self.session)
            logger.debug(f"close session: {self.session} ({rc})")
            self._connected = False

    def reopen_session(self, options=None):
        """Close and reopen the session"""
        self.close_session()
        if options:
            self.open_session(options)
        else:
            self.open_session()

    def _async_method(self, method: str, proxy=None) -> partial:
        """create a patial func to make an async call to a given
        dbus method name
        """
        return partial(self.async_dbus.call, getattr(proxy, method), timeout=1000 * 60 * 20)

    def resolve(self, *args):
        logger.debug(f"DBUS: {self.session_goal.dbus_interface}.resolve()")
        resolve = self._async_method("resolve", proxy=self.session_goal)
        res, err = resolve(dbus.Array())
        return res, err

    def do_transaction(self, options={}):
        logger.debug(f"DBUS: {self.session_goal.dbus_interface}.do_transaction()")
        do_transaction = self._async_method("do_transaction", proxy=self.session_goal)
        options["comment"] = "Yum Extender Transaction"
        res, err = do_transaction(options)
        return res, err

    @dbus_exception
    def confirm_key(self, key_id: str, confirmed: bool):
        return self.session_repo.confirm_key(key_id, confirmed)

    def repo_list(self):
        logger.debug(f"DBUS: {self.session_repo.dbus_interface}.list()")
        get_list = self._async_method("list", proxy=self.session_repo)
        res, err = get_list({"repo_attrs": dbus.Array(["name", "enabled", "priority"]), "enable_disable": "all"})
        return res, err

    def _list_fd(self, options):
        """Generator function that yields packages as they arrive from the server."""

        # create a pipe and pass the write end to the server
        pipe_r, pipe_w = os.pipe()
        # transfer id serves as an identifier of the pipe transfer for a signal emitted
        # after server finish. This example does not use it.
        transfer_id = self.session_rpm.list_fd(options, pipe_w)  # noqa: F841
        # logger.debug(f"list_fd: transfer_id : {transfer_id}")
        # close the write end - otherwise poll cannot detect the end of transmission
        os.close(pipe_w)

        # decoder that will be used to parse incomming data
        parser = json.JSONDecoder()

        # prepare for polling
        poller = select.poll()
        poller.register(pipe_r, select.POLLIN)
        # wait for data 10 secs at most
        timeout = 10000
        # 64k is a typical size of a pipe
        buffer_size = 65536

        # remaining string to parse (can contain unfinished json from previous run)
        to_parse = ""
        # remaining raw data (i.e. data before UTF decoding)
        raw_data = b""
        while True:
            # wait for data
            polled_event = poller.poll(timeout)
            if not polled_event:
                logger.error("Timeout reached.")
                break

            # we know there is only one fd registered in poller
            descriptor, event = polled_event[0]
            # read a chunk of data
            buffer = os.read(descriptor, buffer_size)
            if not buffer:
                # end of file
                break

            raw_data += buffer
            try:
                to_parse += raw_data.decode()
                # decode successful, clear remaining raw data
                raw_data = b""
            except UnicodeDecodeError:
                # Buffer size split data in the middle of multibyte UTF character.
                # Need to read another chunk of data.
                continue

            # parse JSON objects from the string
            while to_parse:
                try:
                    # skip all chars till begin of next JSON objects (new lines mostly)
                    json_obj_start = to_parse.find("{")
                    if json_obj_start < 0:
                        break
                    obj, end = parser.raw_decode(to_parse[json_obj_start:])
                    yield obj
                    to_parse = to_parse[(json_obj_start + end) :]
                except json.decoder.JSONDecodeError:
                    # this is just example which assumes that every decode error
                    # means the data are incomplete (buffer size split the json
                    # object in the middle). So the handler does not do anything
                    # just break the parsing cycle and continue polling.
                    break

    @dbus_exception
    def package_list_fd(self, *args, **kwargs) -> list[list[str]]:
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
        options["with_provides"] = kwargs.pop("with_provides", False)
        options["with_filenames"] = kwargs.pop("with_filenames", False)
        options["with_binaries"] = kwargs.pop("with_binaries", False)
        options["icase"] = True
        options["latest-limit"] = kwargs.pop("latest_limit", 1)
        # limit packages to one of “all”, “installed”, “available”, “upgrades”, “upgradable”
        options["scope"] = kwargs.pop("scope", "all")
        if "repo" in kwargs:
            options["repo"] = kwargs.pop("repo")
        if "arch" in kwargs:
            options["arch"] = kwargs.pop("arch")
        # get and async partial function
        # logger.debug(f" --> options: {options} ")

        # logger.debug(f"DBUS: {self.session_rpm.dbus_interface}.list_fd()")
        result = list(self._list_fd(options))
        logger.debug(f"list_fd({args}) returned : {len(result)} elements")
        return result

    @dbus_exception
    def _test_exception(self):
        """Just for testing purpose"""
        raise dbus.exceptions.DBusException("DBUSError : Something strange in the neighborhood")

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
        options["latest-limit"] = kwargs.pop("latest_limit", 1)
        # limit packages to one of “all”, “installed”, “available”, “upgrades”, “upgradable”
        options["scope"] = kwargs.pop("scope", "all")
        if "repo" in kwargs:
            options["repo"] = kwargs.pop("repo")
        if "arch" in kwargs:
            options["arch"] = kwargs.pop("arch")
        # get and async partial function
        # logger.debug(f" --> options: {options} ")
        logger.debug(f"DBUS: {self.session_rpm.dbus_interface}.list()")
        get_list = self._async_method("list", proxy=self.session_rpm)
        res, err = get_list(options)
        # print(res, err)
        # return as native types.
        if err:
            return [], err
        return res, err

    def advisory_list(self, *args, **kwargs):
        # print(f"\n --> args: {args} kwargs: {kwargs}")
        options = dbus.Dictionary({})
        options["advisory_attrs"] = dbus.Array(kwargs.pop("advisor_attrs"))
        options["contains_pkgs"] = dbus.Array(args)
        options["availability"] = "all"
        # options[""] = get_variant(list[str], [])
        # print(f" --> options: {options} ")
        # print(self.session_advisory)
        logger.debug(f"DBUS: {self.session_advisory.dbus_interface}.list()")
        get_list = self._async_method("list", proxy=self.session_advisory)
        res, err = get_list(options)
        return res, err

    @dbus_exception
    def clean(self, metadata_type):
        result = self.session_base.clean(metadata_type)
        logger.debug(f"clean : {result}")
        return result

    @dbus_exception
    def system_upgrade(self, options):
        logger.debug(f"DBUS: system-upgrade({options})")
        system_upgrade = self._async_method("system_upgrade", proxy=self.session_rpm)
        res, err = system_upgrade(options)
        logger.debug(f"system-upgrade returned : {res, err}")
        return res, err

    @dbus_exception
    def offline_get_status(self):
        """Get the status of the offline update"""
        logger.debug(f"DBUS: {self.session_offline.dbus_interface}.get_status()")
        pending, status = self.session_offline.get_status()
        logger.debug(f"offline_get_status() returned : pending : {pending} stautus :{status}")
        return bool(pending), dict(status)

    @dbus_exception
    def offline_clean(self):
        """Cancel the offline update"""
        logger.debug(f"DBUS: {self.session_offline.dbus_interface}.cancel()")
        clean = self._async_method("clean", proxy=self.session_offline)
        success, err_msg = clean()
        logger.debug(f"clean() returned : success : {success} err_msg : {err_msg}")
        return bool(success), str(err_msg)

    @dbus_exception
    def offline_reboot(self):
        """Reboot the system and install the offline update"""
        logger.debug(f"DBUS: {self.session_offline.dbus_interface}.set_finish_action()")
        reboot = self._async_method("set_finish_action", proxy=self.session_offline)
        success, err_msg = reboot("reboot")
        logger.debug(f"offline_reboot() returned : success : {success} err_msg : {err_msg}")
        return bool(success), str(err_msg)
