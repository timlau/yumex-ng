#!/usr/bin/python3
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
gi.require_version("GLib", "2.0")
gi.require_version("Flatpak", "1.0")

import configparser
import logging
import shutil
import subprocess
import threading
import time
from pathlib import Path

import dbus
import dbus.mainloop.glib
import dbus.service

from gi.repository import AppIndicator3, Flatpak, GLib, Gtk

from yumex.constants import BACKEND

if BACKEND == "DNF5":
    from yumex.service.dnf5 import UpdateChecker
else:
    from yumex.service.dnf4 import UpdateChecker


logger = logging.getLogger("yumex_updater")
logging.basicConfig(
    level=logging.DEBUG,
    format="(%(name)-5s) -  %(message)s",
    datefmt="%H:%M:%S",
)

# Define paths
home_dir = Path.home()
config_dir = home_dir / ".config" / "yumex"
default_config_path = "/usr/share/yumex/yumex-service.conf"
user_config_path = config_dir / "yumex-service.conf"

# Create the config directory if it doesn't exist
config_dir.mkdir(parents=True, exist_ok=True)

# Copy the default config file if the user config file doesn't exist
if not user_config_path.exists():
    shutil.copy(default_config_path, user_config_path)

# Read configuration file
config = configparser.ConfigParser()
config.read(user_config_path)

custom_updater = config.get("DEFAULT", "custom_updater", fallback=None)
always_hide = config.getboolean("DEFAULT", "always_hide", fallback=False)
update_sync_interval = config.getint("DEFAULT", "update_sync_interval", fallback=3600)


class UpdateService(dbus.service.Object):
    def __init__(self, bus_name: dbus.service.BusName, object_path: str) -> None:
        super().__init__(bus_name, object_path)

    @dbus.service.method("com.yumex.UpdateService")
    def RefreshUpdates(self) -> None:
        refresh_updates()


def on_clicked_update(widget: Gtk.Widget) -> None:
    if custom_updater:
        subprocess.Popen([custom_updater])


def on_clicked_pm(widget: Gtk.Widget) -> None:
    subprocess.Popen(["/usr/bin/yumex"])


def refresh_updates(widget: Gtk.Widget = None) -> None:
    logger.debug("Refreshing updates")
    sys_update_count = len(UpdateChecker())

    flatpak_user_count = len(Flatpak.Installation.new_user().list_installed_refs_for_update())
    flatpak_sys_count = len(Flatpak.Installation.new_system().list_installed_refs_for_update())

    update_count = sys_update_count + flatpak_user_count + flatpak_sys_count

    logger.debug(f" --> flatpak system : {flatpak_sys_count}")
    logger.debug(f" --> flatpak user   : {flatpak_user_count}")
    logger.debug(f" --> system         : {update_count}")

    hover_text_lines = ["There are updates available:"]
    if sys_update_count > 0:
        hover_text_lines.append(f"  System: {sys_update_count}")
    if flatpak_user_count > 0:
        hover_text_lines.append(f"  Flatpak (user): {flatpak_user_count}")
    if flatpak_sys_count > 0:
        hover_text_lines.append(f"  Flatpak (system): {flatpak_sys_count}")
    hover_text = "\n".join(hover_text_lines)

    if not always_hide:
        if update_count > 0:
            GLib.idle_add(indicator.set_title, hover_text)
            GLib.idle_add(indicator.set_status, AppIndicator3.IndicatorStatus.ACTIVE)
        else:
            GLib.idle_add(indicator.set_status, AppIndicator3.IndicatorStatus.PASSIVE)


def check_updates() -> None:
    while True:
        refresh_updates()
        time.sleep(update_sync_interval)


indicator = AppIndicator3.Indicator.new(
    "System Update Monitor",
    "/usr/share/icons/hicolor/scalable/apps/yumex-system-software-update.svg",
    AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
)
indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
indicator.set_title("Checking for updates...")

menu = Gtk.Menu()

refresh_item = Gtk.MenuItem(label="Check for Updates")
refresh_item.connect("activate", refresh_updates)
menu.append(refresh_item)

if custom_updater:
    update_item = Gtk.MenuItem(label="Update System")
    update_item.connect("activate", on_clicked_update)
    menu.append(update_item)

pm_item = Gtk.MenuItem(label="Open Package Manager")
pm_item.connect("activate", on_clicked_pm)
menu.append(pm_item)

menu.show_all()

indicator.set_menu(menu)

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
session_bus = dbus.SessionBus()
bus_name = dbus.service.BusName("com.yumex.UpdateService", session_bus)
update_service = UpdateService(bus_name, "/com/yumex/UpdateService")

refresh_updates()

update_thread = threading.Thread(target=check_updates, daemon=True)
update_thread.start()

Gtk.main()
