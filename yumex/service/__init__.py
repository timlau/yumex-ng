# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2024 Tim Lauridsen

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
gi.require_version("Flatpak", "1.0")


import configparser
import shutil
import logging
from pathlib import Path
from dataclasses import dataclass

from gi.repository import AppIndicator3, Gtk, Flatpak  # type: ignore
from yumex.constants import BACKEND

if BACKEND == "DNF5":
    from yumex.service.dnf5 import check_dnf_updates
else:
    from yumex.service.dnf4 import check_dnf_updates


logger = logging.getLogger("yumex_updater")


@dataclass
class Config:
    custom_updater: str
    always_hide: bool
    update_sync_interval: int
    send_notification: bool

    @classmethod
    def from_file(cls):
        # Define paths
        config_dir = Path.home() / ".config" / "yumex"
        default_config_path = "/usr/share/yumex/yumex-service.conf"
        user_config_path = config_dir / "yumex-service.conf"
        # Create the config directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        # Copy the default config file if the user config file doesn't exist
        if not user_config_path.exists():
            shutil.copy(default_config_path, user_config_path)

        # Read configuration file
        logger.debug(f"CONFIG: Loading config from {user_config_path}")
        config = configparser.ConfigParser()
        config.read(user_config_path)
        custom_updater = config.get("DEFAULT", "custom_updater", fallback=None)
        always_hide = config.getboolean("DEFAULT", "always_hide", fallback=False)
        update_sync_interval = config.getint("DEFAULT", "update_sync_interval", fallback=3600)
        notification = config.getboolean("DEFAULT", "send_notification", fallback=False)
        logger.debug(f"CONFIG: custom_updater        = {custom_updater}")
        logger.debug(f"CONFIG: always_hide           = {always_hide}")
        logger.debug(f"CONFIG: update_sync_interval  = {update_sync_interval}")
        logger.debug(f"CONFIG: send_notification     = {notification}")
        return cls(custom_updater, always_hide, update_sync_interval, notification)


class Indicator:
    def __init__(self):
        self._indicator = None

    @property
    def indicator(self):
        if not self._indicator:
            self._indicator = self._factory()
        return self._indicator

    def clear(self):
        del self._indicator
        self._indicator = None

    def _factory(self):
        try:
            indicator = AppIndicator3.Indicator.new(
                "System Update Monitor",
                "/usr/share/icons/hicolor/scalable/apps/yumex-system-software-update.svg",
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            )
            indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            indicator.set_title("Checking for updates...")
            indicator.set_menu(self.get_menu())
            return indicator
        except Exception:
            logger.error("Error in creating AppIndicator", exc_info=True)

    def on_clicked_custom(self, *args) -> None:
        """start custom updater"""
        subprocess.Popen([CONFIG.custom_updater], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def on_clicked_pm(self, *args) -> None:
        """start yumex"""
        subprocess.Popen(["/usr/bin/yumex", "--update"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def on_check_updates(self, *args) -> None:
        refresh_updates(True)

    def set_title(self, title):
        indicator = self.indicator
        if indicator:
            indicator.set_title(title)

    def get_menu(self) -> Gtk.Menu:
        """build menu for sys tray indicator"""
        menu = Gtk.Menu()
        refresh_item = Gtk.MenuItem(label="Check for Updates")
        refresh_item.connect("activate", self.on_check_updates)
        menu.append(refresh_item)
        if CONFIG.custom_updater:
            update_item = Gtk.MenuItem(label="Update System")
            update_item.connect("activate", self.on_clicked_custom)
            menu.append(update_item)
        pm_item = Gtk.MenuItem(label="Open Package Manager")
        pm_item.connect("activate", self.on_clicked_pm)
        menu.append(pm_item)
        menu.show_all()
        return menu


@dataclass
class Updates:
    sys_update_count: int
    flatpak_user_count: int
    flatpak_sys_count: int

    @classmethod
    def get_updates(cls, refresh):
        sys_update_count = len(check_dnf_updates(refresh))
        user_installation = Flatpak.Installation.new_user()
        flatpak_user_count = len(user_installation.list_installed_refs_for_update())
        del user_installation

        system_installation = Flatpak.Installation.new_system()
        flatpak_sys_count = len(system_installation.list_installed_refs_for_update())
        del system_installation
        return cls(sys_update_count, flatpak_user_count, flatpak_sys_count)
