import logging
from functools import partial
from logging import getLogger
from typing import Self, Any
from dasbus.connection import SystemMessageBus
from dasbus.identifier import DBusServiceIdentifier
from dasbus.loop import EventLoop
from dasbus.error import DBusError  # noqa
from dasbus.typing import get_native, get_variant, Variant  # noqa: F401

# from gi.repository import GLib  # type: ignore


# Constants
SYSTEM_BUS = SystemMessageBus()
DNFDBUS_NAMESPACE = ("org", "rpm", "dnf", "v0")
DNFDBUS = DBusServiceIdentifier(namespace=DNFDBUS_NAMESPACE, message_bus=SYSTEM_BUS)
ASYNC_TIMEOUT = 20 * 60 * 1000  # 20 min in ms

logger = getLogger("dnf5dbus")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s",
    datefmt="%H:%M:%S",
)


# GLib.Variant converters
def gv_list(var: list[str]) -> Variant:
    return get_variant(list[str], var)


def gv_string(var: str) -> Variant:
    return get_variant(str, var)


# async call handler class
class AsyncDbusCaller:
    def __init__(self) -> None:
        self.res = None
        self.loop = None

    def callback(self, call) -> None:
        try:
            self.res = call()
        except DBusError as e:
            msg = str(e)
            match msg:
                # This occours on long running transaction
                case "Remote peer disconnected":
                    logger.error("Connection to dns5daemon lost")
                    self.res = None
                # This occours when PolicyKet autherization is not given before a time limit
                case "Method call timed out":
                    logger.error("Dbus method call timeout")
                    self.res = "PolicyKit Autherisation failed"
                # This occours when PolicyKet autherization dialog is cancelled
                case "Not authorized":
                    logger.error("PolicyKit Autherisation failed")
                    self.res = "PolicyKit Autherisation failed"
                case _:
                    logger.error(f"Error in dbus call : {msg}")
        self.loop.quit()

    def call(self, mth, *args, **kwargs) -> Any:
        self.loop = EventLoop()
        # timeout = 10min
        mth(*args, timeout=ASYNC_TIMEOUT, **kwargs, callback=self.callback)
        self.loop.run()
        if self.res:
            return get_native(self.res)
        return None


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
        do_transaction(options)

    def confirm_key(self, *args):
        return self.session.confirm_key(*args)
