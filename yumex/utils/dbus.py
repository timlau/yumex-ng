from dasbus.connection import SessionMessageBus
from dasbus.error import DBusError
from dasbus.identifier import DBusServiceIdentifier
from dasbus.typing import get_native
from typing import Any
from dasbus.loop import EventLoop
from dasbus.error import DBusError  # noqa

from yumex.utils import log

BUS = SessionMessageBus()
SYSTEMD_NAMESPACE = ("org", "freedesktop", "systemd1")
SYSTEMD = DBusServiceIdentifier(namespace=SYSTEMD_NAMESPACE, message_bus=BUS)

YUMEX_UPDATER_NAMESPACE = ("dk", "yumex", "UpdateService")
YUMEX_UPDATER = DBusServiceIdentifier(namespace=YUMEX_UPDATER_NAMESPACE, message_bus=BUS)
ASYNC_TIMEOUT = 20 * 60 * 1000  # 20 min in ms


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
            # convert Variant return vlaues to native python format
            return get_native(self.res)
        return None


def is_user_service_running(service_name):
    try:
        systemd = SYSTEMD.get_proxy(interface_name="org.freedesktop.systemd1.Manager")
        unit_path = systemd.GetUnit(service_name)
        log(f"DBus: systemd service object: {unit_path}")
        unit = SYSTEMD.get_proxy(unit_path)
        state = get_native(unit.Get("org.freedesktop.systemd1.Unit", "SubState"))
        log(f"DBus: {service_name} is {state}")
        return state == "running"
    except DBusError as e:
        log(f"DBus Error: {e}")
        return False


def sync_updates(refresh: bool = True):
    service_name = "yumex-updater-systray.service"

    if is_user_service_running(service_name):
        try:
            async_call = AsyncDbusCaller().call
            updater = YUMEX_UPDATER.get_proxy()
            async_call(updater.RefreshUpdates, refresh)
            log("(sync_updates) triggered updater checker refresh")
        except DBusError as e:
            log(f"DBus Error: {e}")
    else:
        log(f"(sync_updates) The service {service_name} is not running.")


if __name__ == "__main__":
    sync_updates()
