import logging
from typing import Any

from dasbus.connection import SessionMessageBus
from dasbus.error import DBusError  # noqa
from dasbus.identifier import DBusServiceIdentifier
from dasbus.loop import EventLoop
from dasbus.typing import get_native

from yumex.utils import timed

logger = logging.getLogger(__name__)

BUS = SessionMessageBus()
SYSTEMD_NAMESPACE = ("org", "freedesktop", "systemd1")
SYSTEMD = DBusServiceIdentifier(namespace=SYSTEMD_NAMESPACE, message_bus=BUS)

YUMEX_UPDATER_NAMESPACE = ("dk", "yumex", "UpdateService")
YUMEX_UPDATER = DBusServiceIdentifier(namespace=YUMEX_UPDATER_NAMESPACE, message_bus=BUS)


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
                # This could occours on long running transaction
                case "Remote peer disconnected":
                    logger.debug("DbusError: Connection to dns5daemon lost")
                    self.res = None
                # This occours when PolicyKet autherization is not given before a time limit
                case "Method call timed out":
                    logger.debug("DbusError: Dbus method call timeout")
                    self.res = "PolicyKit Autherisation failed"
                # This occours when PolicyKet autherization dialog is cancelled
                case "Not authorized":
                    logger.debug("DbusError: PolicyKit Autherisation failed")
                    self.res = "PolicyKit Autherisation failed"
                case _:
                    logger.debug(f"DbusError: Error in dbus call : {msg}")
                    self.res = None
        except TimeoutError:  # This could occours when a transaction takes too long
            logger.debug("TimeoutError: The call timed out!")
            self.res = "DBus Timeout error"
        self.loop.quit()

    def call(self, mth, *args, **kwargs) -> Any:
        self.loop = EventLoop()
        # timeout = 10min
        logger.debug(f" --> ASyncDbus: calling {mth} args: {args}")
        mth(*args, **kwargs, callback=self.callback)
        self.loop.run()
        if self.res:
            # convert Variant return vlaues to native python format
            return get_native(self.res)
        return None


def is_user_service_running(service_name):
    try:
        async_caller = AsyncDbusCaller()
        systemd = SYSTEMD.get_proxy(interface_name="org.freedesktop.systemd1.Manager")
        unit_path = async_caller.call(systemd.GetUnit, service_name)
        logger.debug(f"DBus: systemd service object: {unit_path}")
        unit = SYSTEMD.get_proxy(unit_path)
        state = get_native(async_caller.call(unit.Get, "org.freedesktop.systemd1.Unit", "SubState"))
        logger.debug(f"DBus: {service_name} is {state}")
        return state == "running"
    except DBusError as e:
        logger.debug(f"DBus Error: {e}")
        return False


@timed
def sync_updates(refresh: bool = False):
    service_name = "yumex-updater-systray.service"

    logger.debug("(sync_updates) check updater service is running")  # FIXME: Debug logging
    if is_user_service_running(service_name):
        try:
            logger.debug("(sync_updates) getting DBus proxy ")  # FIXME: Debug logging
            updater = YUMEX_UPDATER.get_proxy()
            logger.debug("(sync_updates) got DBus proxy ")  # FIXME: Debug logging
            async_caller = AsyncDbusCaller()
            logger.debug("(sync_updates) calling RefreshUpdates")  # FIXME: Debug logging
            async_caller.call(updater.RefreshUpdates, refresh)
            logger.debug("(sync_updates) triggered updater checker refresh")
            return True, "RefreshUpdates triggered"
        except DBusError as e:
            logger.debug(f"DBus Error: {e}")
            return False, f"DBusError : {str(e)}"
    else:
        logger.debug(f"(sync_updates) The service {service_name} is not running.")
        return False, "yumex-updater-systray not running"


if __name__ == "__main__":
    from yumex.utils import setup_logging

    setup_logging()
    # is_user_service_running("dconf.service")
    sync_updates()
