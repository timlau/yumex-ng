from functools import partial
from logging import getLogger
from typing import Self

from dasbus.connection import SystemMessageBus
from dasbus.identifier import DBusServiceIdentifier
from dasbus.typing import Variant, get_native, get_variant  # noqa: F401
from dasbus.unix import GLibClientUnix

from yumex.utils.dbus import AsyncDbusCaller

# from gi.repository import GLib  # type: ignore


# Constants
SYSTEM_BUS = SystemMessageBus()
DNFDBUS_NAMESPACE = ("org", "rpm", "dnf", "v0")
DNFDBUS = DBusServiceIdentifier(namespace=DNFDBUS_NAMESPACE, message_bus=SYSTEM_BUS)

logger = getLogger(__name__)


def gv_list(var: list[str]) -> Variant:
    """convert list of strings to a Variant of type (as)"""
    return get_variant(list[str], var)


class Dnf5DbusClient:
    """context manager for calling the dnf5daemon dbus API

    https://dnf5.readthedocs.io/en/latest/dnf_daemon/dnf5daemon_dbus_api.8.html#interfaces
    """

    def __init__(self) -> None:
        # setup the dnf5daemon dbus proxy
        self.proxy = DNFDBUS.get_proxy(client=GLibClientUnix)
        self.async_dbus = AsyncDbusCaller()

    def __enter__(self) -> Self:
        """context manager enter, return current object"""
        # get a session path for the dnf5daemon
        self.session_path = self.proxy.open_session({})
        # setup a proxy for the session object path
        # self.session = DNFDBUS.get_proxy(self.session_path)
        dnf_interface = ".".join(DNFDBUS_NAMESPACE)
        self.session_repo = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.rpm.Repo")
        self.session_rpm = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.rpm.Rpm")
        self.session_goal = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.Goal")
        self.session_base = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.Base")
        self.session_group = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.comps.Group")
        self.session_advisory = DNFDBUS.get_proxy(self.session_path, interface_name=f"{dnf_interface}.Advisory")
        logger.debug(f"Open Dnf5Daemon session: {self.session_path}")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """context manager exit"""
        self.proxy.close_session(self.session_path)
        logger.debug(f"Close Dnf5Daemon session: {self.session_path}")
        if exc_type:
            logger.critical("", exc_info=(exc_type, exc_value, exc_traceback))
        # close dnf5 session

    def _async_method(self, method: str, proxy) -> partial:
        """create a patial func to make an async call to a given
        dbus method name
        """
        return partial(self.async_dbus.call, getattr(proxy, method))

    def resolve(self, *args):
        resolve = self._async_method("resolve", proxy=self.session_goal)
        return resolve(*args)

    def do_transaction(self):
        do_transaction = self._async_method("do_transaction", proxy=self.session_goal)
        options = {"comment": get_variant(str, "Yum Extender Transaction")}
        return do_transaction(options)

    def confirm_key(self, *args):
        return self.session_repo.confirm_key(*args)

    def package_list(self, *args, **kwargs) -> list[list[str]]:
        """call the org.rpm.dnf.v0.rpm.Repo list method

        *args is package patterns to match
        **kwargs can contain other options like package_attrs, repo or scope

        """
        logger.debug(f"\n --> args: {args} kwargs: {kwargs}")
        package_attrs = kwargs.pop("package_attrs", ["nevra"])
        options = {}
        options["patterns"] = get_variant(list[str], args)  # gv_list(args)
        options["package_attrs"] = get_variant(list[str], package_attrs)
        options["with_src"] = get_variant(bool, False)
        options["with_nevra"] = get_variant(bool, kwargs.pop("with_nevra", True))
        options["with_provides"] = get_variant(bool, kwargs.pop("with_provides", False))
        options["with_filenames"] = get_variant(bool, kwargs.pop("with_filenames", False))
        options["with_binaries"] = get_variant(bool, kwargs.pop("with_binaries", False))
        options["icase"] = get_variant(bool, True)
        options["latest-limit"] = get_variant(int, 1)
        # limit packages to one of “all”, “installed”, “available”, “upgrades”, “upgradable”
        options["scope"] = get_variant(str, kwargs.pop("scope", "all"))
        if "repo" in kwargs:
            options["repo"] = get_variant(list[str], kwargs.pop("repo"))
        # get and async partial function
        logger.debug(f" --> options: {options} ")
        package_attrs = kwargs.pop("package_attrs", ["nevra"])
        get_list = self._async_method("list", proxy=self.session_rpm)
        result = get_list(options)
        # return as native types.
        return get_native(result)
