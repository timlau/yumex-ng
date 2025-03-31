import logging

import dbus

UPDATER_BUS_NAME = "dk.yumex.UpdateService"
UPDATER_OBJECT_PATH = "/" + UPDATER_BUS_NAME.replace(".", "/")

logger = logging.getLogger(__name__)


def sync_updates(refresh: bool = False):
    try:
        bus = dbus.SessionBus()
        updater_iface = dbus.Interface(
            bus.get_object(UPDATER_BUS_NAME, UPDATER_OBJECT_PATH),
            dbus_interface=UPDATER_BUS_NAME,
        )
        updater_iface.RefreshUpdates(True)
        logger.debug(f"{UPDATER_BUS_NAME}.RefreshUpdates called")

    except dbus.DBusException as e:
        match e.get_dbus_name():
            case "org.freedesktop.DBus.Error.ServiceUnknown":
                logger.debug(f" {UPDATER_BUS_NAME} is not running")
            case _:
                logger.debug(e.get_dbus_message())
                logger.debug(e.get_dbus_name())


if __name__ == "__main__":
    from yumex.utils import setup_logging

    setup_logging()
    # is_user_service_running("dconf.service")
    sync_updates()
