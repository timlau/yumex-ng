from dasbus.connection import SessionMessageBus
from dasbus.error import DBusError
from dasbus.identifier import DBusServiceIdentifier
from dasbus.typing import get_native

from yumex.utils import log

BUS = SessionMessageBus()
SYSTEMD_NAMESPACE = ("org", "freedesktop", "systemd1")
SYSTEMD = DBusServiceIdentifier(namespace=SYSTEMD_NAMESPACE, message_bus=BUS)

YUMEX_UPDATER_NAMESPACE = ("dk", "yumex", "UpdateService")
YUMEX_UPDATER = DBusServiceIdentifier(namespace=YUMEX_UPDATER_NAMESPACE, message_bus=BUS)


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


def sync_updates():
    service_name = "yumex-updater-systray.service"

    if is_user_service_running(service_name):
        try:
            updater = YUMEX_UPDATER.get_proxy()
            updater.RefreshUpdates()
            log("(sync_updates) triggered updater checker refresh")
        except DBusError as e:
            log(f"DBus Error: {e}")
    else:
        log(f"(sync_updates) The service {service_name} is not running.")


if __name__ == "__main__":
    sync_updates()
