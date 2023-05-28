import logging
from functools import partial
from logging import getLogger
from typing import Self, Any
from dasbus.connection import SystemMessageBus
from dasbus.identifier import DBusServiceIdentifier
from dasbus.loop import EventLoop
from dasbus.error import DBusError
from gi.repository import GLib  # type: ignore


# Constants
SYSTEM_BUS = SystemMessageBus()
DNFDBUS_NAMESPACE = ("org", "rpm", "dnf", "v0")
DNFDBUS = DBusServiceIdentifier(namespace=DNFDBUS_NAMESPACE, message_bus=SYSTEM_BUS)

logger = getLogger("dnf5dbus")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s",
    datefmt="%H:%M:%S",
)


# GLib.Variant converters
def gv_list(var: list[str]) -> GLib.Variant:
    return GLib.Variant("as", var)


def gv_str(var: str) -> GLib.Variant:
    return GLib.Variant("s", var)


def gv_bool(var: bool) -> GLib.Variant:
    return GLib.Variant("b", var)


def gv_int(var: int) -> GLib.Variant:
    return GLib.Variant("i", var)


# async call handler class
class AsyncDbusCaller:
    def __init__(self) -> None:
        self.res = None
        self.loop = None

    def callback(self, call) -> None:
        self.res = call()
        self.loop.quit()

    def call(self, mth, *args, **kwargs) -> Any:
        self.loop = EventLoop()
        mth(*args, **kwargs, callback=self.callback)
        self.loop.run()
        return self.res


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

    def package_list(self, *args, **kwargs) -> list[list[str]]:
        """call the org.rpm.dnf.v0.rpm.Repo list method

        *args is package patterns to match
        **kwargs can contain other options like package_attrs, repo or scope

        """
        options = {}
        options["patterns"] = gv_list(args)
        options["package_attrs"] = gv_list(kwargs.pop("package_attrs", ["nevra"]))
        options["with_src"] = gv_bool(False)
        options["latest-limit"] = gv_int(1)
        if "repo" in kwargs:
            options["repo"] = gv_list(kwargs.pop("repo"))
        if "scope" in kwargs:
            options["scope"] = gv_str(kwargs.pop("scope"))
        # get and async partial function
        get_list = self._async_method("list")
        result = get_list(options)
        # [{
        #   "id": GLib.Variant(),
        #   "nevra": GLib.Variant("s", nevra),
        #   "repo": GLib.Variant("s", repo),
        #   },
        #   {....},
        # ]
        return [
            [value.get_string() for value in list(elem.values())[1:]] for elem in result
        ]


# dnf5daemon-server is needed to work
if __name__ == "__main__":
    with Dnf5DbusClient() as client:
        # print(client.session.Introspect())
        key = "0xFFFF"
        print(f"Searching for {key}")
        pkgs = client.package_list(
            key,
            package_attrs=["nevra", "repo_id"],
            repo=["fedora", "updates"],
        )
        print(f"Found : {len(pkgs)}")
        for nevra, repo in pkgs:
            print(f"FOUND: {nevra:40} repo: {repo}")
            print("removeing")
            to_remove = gv_list([nevra])
            client.session.remove(to_remove, {})
        if len(pkgs) > 0:
            try:
                print("depsolve")
                res = client.session.resolve({})
                print(res)
                print("do transaction")
                res = client.session.do_transaction({})
                print(res)
            except DBusError as e:
                print(10 * "=" + "> Error calling dnf5daemon :")
                print(e)
