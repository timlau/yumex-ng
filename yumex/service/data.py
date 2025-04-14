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

import logging
import os
import subprocess
from dataclasses import dataclass

import gi

from yumex.constants import APP_ID
from yumex.service.dnf5daemon import Dnf5UpdateChecker

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
gi.require_version("Flatpak", "1.0")

from gi.repository import AppIndicator3, Flatpak, Gio, Gtk  # type: ignore  # noqa: E402

logger = logging.getLogger("yumex_updater")


def open_yumex(action="", pkgs=0, flatpaks=0):
    """launch yumex"""
    logger.info(f"open_yumex action: {action} pkgs: {pkgs} flatpaks: {flatpaks}")
    env = os.environ.copy()
    if pkgs:
        subprocess.Popen(["/usr/bin/yumex", "--update"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    else:
        subprocess.Popen(["/usr/bin/yumex", "--flatpak"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)


@dataclass
class Config:
    custom_updater: str
    show_icon: bool
    update_sync_interval: int
    send_notification: bool
    dark_icon: bool

    @classmethod
    def from_gsettings(cls):
        logger.debug("CONFIG: Loading config from gsettings")
        settings: Gio.Settings = Gio.Settings(APP_ID)
        custom_updater = settings.get_string("upd-custom")
        show_icon = settings.get_boolean("upd-show-icon")
        update_interval = settings.get_int("upd-interval")
        notification = settings.get_boolean("upd-notification")
        dark_icon = settings.get_boolean("upd-dark-icon")
        logger.debug(f"CONFIG: custom_updater        = {custom_updater}")
        logger.debug(f"CONFIG: show_icon             = {show_icon}")
        logger.debug(f"CONFIG: update_sync_interval  = {update_interval}")
        logger.debug(f"CONFIG: send_notification     = {notification}")
        logger.debug(f"CONFIG: dark_icon             = {dark_icon}")
        return cls(custom_updater, show_icon, update_interval, notification, dark_icon)


class Indicator:
    def __init__(self, custom_updater, refresh_func, dark_icon):
        self._indicator = None
        self.custom_updater = custom_updater
        self.dark_icon = dark_icon
        self.refresh_func = refresh_func
        self.last_pkgs = 0
        self.last_flatpaks = 0

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
            if self.dark_icon:
                logger.debug("Using dark icon")
                icon_name = "yumex-update-dark-symbolic.svg"
            else:
                icon_name = "yumex-update-symbolic.svg"
            indicator = AppIndicator3.Indicator.new(
                "System Update Monitor",
                f"/usr/share/icons/hicolor/scalable/apps/{icon_name}",
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
        env = os.environ.copy()
        custom_updater_args = self.custom_updater.split()
        subprocess.Popen(custom_updater_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

    def on_clicked_pm(self, *args) -> None:
        """start yumex"""
        open_yumex("open-yumex", self.last_pkgs, self.last_flatpaks)

    def on_check_updates(self, *args) -> None:
        self.refresh_func(True)

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
        if self.custom_updater:
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
        with Dnf5UpdateChecker() as checker:
            sys_update_count = len(checker.check_updates(refresh))
        user_installation = Flatpak.Installation.new_user()
        flatpak_user_count = len(user_installation.list_installed_refs_for_update())
        del user_installation

        system_installation = Flatpak.Installation.new_system()
        flatpak_sys_count = len(system_installation.list_installed_refs_for_update())
        del system_installation
        return cls(sys_update_count, flatpak_user_count, flatpak_sys_count)
