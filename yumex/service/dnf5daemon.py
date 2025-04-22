import logging
from typing import Generator

import dbus

from yumex.backend.dnf import YumexPackage
from yumex.backend.dnf5daemon import PACKAGE_ATTRS, create_package
from yumex.backend.dnf5daemon.filter import FilterUpdates

DNFDAEMON_BUS_NAME = "org.rpm.dnf.v0"
DNFDAEMON_OBJECT_PATH = "/" + DNFDAEMON_BUS_NAME.replace(".", "/")

IFACE_SESSION_MANAGER = "{}.SessionManager".format(DNFDAEMON_BUS_NAME)
IFACE_REPO = "{}.rpm.Repo".format(DNFDAEMON_BUS_NAME)
IFACE_RPM = "{}.rpm.Rpm".format(DNFDAEMON_BUS_NAME)
IFACE_GOAL = "{}.Goal".format(DNFDAEMON_BUS_NAME)
IFACE_BASE = "{}.Base".format(DNFDAEMON_BUS_NAME)
IFACE_GROUP = "{}.comps.Group".format(DNFDAEMON_BUS_NAME)
IFACE_ADVISORY = "{}.Advisory".format(DNFDAEMON_BUS_NAME)

logger = logging.getLogger(__name__)
SYSTEM_BUS = dbus.SystemBus()


class Dnf5UpdateChecker:
    def __init__(self):
        self.session = None

    def __enter__(self):
        """Enter the context manager"""
        self.session = self.open_session()
        if self.session:
            self.iface_rpm = dbus.Interface(
                SYSTEM_BUS.get_object(DNFDAEMON_BUS_NAME, self.session), dbus_interface=IFACE_RPM
            )
            self.iface_repo = dbus.Interface(
                SYSTEM_BUS.get_object(DNFDAEMON_BUS_NAME, self.session), dbus_interface=IFACE_REPO
            )
            return self
        else:
            logger.error("Failed to open dnf5daemon session")
            return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager"""
        if self.session:
            try:
                self.close_session(self.session)
            except Exception as e:
                logger.error(f"Failed to close dnf5daemon session: {e}")
        self.session = None
        return False  # Do not suppress exceptions

    def open_session(self) -> Generator[tuple[dbus.SystemBus, str], None, None]:
        """Get a new session with dnf5daemon-server"""
        try:
            iface_session = dbus.Interface(
                SYSTEM_BUS.get_object(DNFDAEMON_BUS_NAME, DNFDAEMON_OBJECT_PATH),
                dbus_interface=IFACE_SESSION_MANAGER,
            )
            session = iface_session.open_session(dbus.Dictionary({}, signature=dbus.Signature("sv")))
            logger.debug(f"Open dnf5daemon session : {session}")
            return session
        except dbus.DBusException as e:
            logger.error(e)
            return None

    def close_session(self, session):
        try:
            iface_session = dbus.Interface(
                SYSTEM_BUS.get_object(DNFDAEMON_BUS_NAME, DNFDAEMON_OBJECT_PATH),
                dbus_interface=IFACE_SESSION_MANAGER,
            )
            iface_session.close_session(session)
            logger.debug(f"Close dnf5daemon session : {session}")
        except dbus.DBusException as e:
            logger.error(e)

    def get_packages_by_name(self, pkg: YumexPackage) -> list:
        """Get a list of packages by name"""
        try:
            options = {
                "package_attrs": dbus.Array(PACKAGE_ATTRS),
                "scope": "available",
                "patterns": dbus.Array([pkg.name]),
                "latest-limit": 10,
                "with_src": False,
                "arch": [pkg.arch],
            }
            res = self.iface_rpm.list(options)
            if res is None:
                logger.error("No packages found")
                return []
            pkgs = self.get_yumex_packages(res)
            return pkgs
        except dbus.DBusException as e:
            logger.error(e)
            logger.debug(f"Options: {options}")
            return []

    def get_repo_priorities(self) -> list:
        """Get a list of repositories"""
        try:
            repos = self.iface_repo.list(
                {
                    "repo_attrs": dbus.Array(["priority"]),
                    "enable_disable": "enabled",
                }
            )
            repo_prioritiy = {str(repo["id"]): int(repo["priority"]) for repo in repos}
            return repo_prioritiy
        except dbus.DBusException as e:
            logger.error(e)
            return []

    def get_yumex_packages(self, pkgs: list) -> list:
        """Convert a list of packages to YumexPackage objects"""
        yumex_pkgs = [create_package(pkg) for pkg in pkgs]
        return yumex_pkgs

    def check_updates(self, refresh: bool = False) -> list:
        try:
            options = {
                "package_attrs": dbus.Array(PACKAGE_ATTRS),
                "scope": "upgrades",
                "patterns": dbus.Array(["*"]),
                "latest-limit": 1,
            }
            pkgs = self.get_yumex_packages(self.iface_rpm.list(options))
            repo_priorities = self.get_repo_priorities()
            updates = FilterUpdates(repo_priorities, self.get_packages_by_name).get_updates(pkgs)
            return updates
        except dbus.Exception as e:
            logger.error(e)
            return []
