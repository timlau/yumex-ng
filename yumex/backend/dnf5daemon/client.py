from functools import partial
from logging import getLogger
from typing import Self

from dasbus.connection import SystemMessageBus
from dasbus.identifier import DBusServiceIdentifier
from dasbus.typing import Variant, get_native, get_variant  # noqa: F401

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
        self.proxy = DNFDBUS.get_proxy()
        self.async_dbus = AsyncDbusCaller()

    def __enter__(self) -> Self:
        """context manager enter, return current object"""
        # get a session path for the dnf5daemon
        self.session_path = self.proxy.open_session({})
        # setup a proxy for the session object path
        self.session = DNFDBUS.get_proxy(self.session_path)
        logger.debug(f"Open Dnf5Daemon session: {self.session_path}")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """context manager exit"""
        self.proxy.close_session(self.session_path)
        logger.debug(f"Close Dnf5Daemon session: {self.session_path}")
        if exc_type:
            logger.critical("", exc_info=(exc_type, exc_value, exc_traceback))
        # close dnf5 session

    def _async_method(self, method: str) -> partial:
        """create a patial func to make an async call to a given
        dbus method name
        """
        return partial(self.async_dbus.call, getattr(self.session, method))

    def resolve(self, *args):
        resolve = self._async_method("resolve")
        return resolve(*args)

    def do_transaction(self):
        do_transaction = self._async_method("do_transaction")
        options = {"comment": get_variant(str, "Yum Extender Transaction")}
        return do_transaction(options)

    def confirm_key(self, *args):
        return self.session.confirm_key(*args)
