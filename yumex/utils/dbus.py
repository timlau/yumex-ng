import dbus
from dbus.exceptions import DBusException

from yumex.utils import log


def is_user_service_running(service_name):
    try:
        # Connect to the user bus
        bus = dbus.SessionBus()
        # Get the systemd service manager object
        systemd = bus.get_object("org.freedesktop.systemd1", "/org/freedesktop/systemd1")
        manager = dbus.Interface(systemd, "org.freedesktop.systemd1.Manager")
        # Get the unit status
        unit_path = manager.GetUnit(service_name)
        unit = bus.get_object("org.freedesktop.systemd1", unit_path)
        unit_properties = dbus.Interface(unit, "org.freedesktop.DBus.Properties")
        # Check the SubState of the service
        sub_state = unit_properties.Get("org.freedesktop.systemd1.Unit", "SubState")
        return sub_state == "running"
    except DBusException as e:
        log(f"(sync_updates) Error checking service status: {e}")
        return False


def sync_updates():
    service_name = "yumex-updater-systray.service"

    if is_user_service_running(service_name):
        try:
            # Connect to the session bus
            bus = dbus.SessionBus()
            # Get the object
            tray_icon_object = bus.get_object("com.yumex.UpdateService", "/com/yumex/UpdateService")
            # Get the interface
            tray_icon_interface = dbus.Interface(tray_icon_object, "com.yumex.UpdateService")
            # Call the RefreshUpdates method
            tray_icon_interface.RefreshUpdates()
        except DBusException as e:
            log(f"(sync_updates) DBusException: {e}")
            # Handle the exception or log it as needed
    else:
        log(f"(sync_updates) The service {service_name} is not running.")
