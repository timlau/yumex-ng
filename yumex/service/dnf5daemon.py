import logging
from functools import partial
from typing import Generator

import dbus

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


def open_session() -> Generator[tuple[dbus.SystemBus, str], None, None]:
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


def close_session(session):
    try:
        iface_session = dbus.Interface(
            SYSTEM_BUS.get_object(DNFDAEMON_BUS_NAME, DNFDAEMON_OBJECT_PATH),
            dbus_interface=IFACE_SESSION_MANAGER,
        )
        iface_session.close_session(session)
        logger.debug(f"Close dnf5daemon session : {session}")
    except dbus.DBusException as e:
        logger.error(e)


def get_packages_by_name(session, package_name: str) -> list:
    """Get a list of packages by name"""
    try:
        iface_rpm = dbus.Interface(SYSTEM_BUS.get_object(DNFDAEMON_BUS_NAME, session), dbus_interface=IFACE_RPM)
        options = {
            "package_attrs": dbus.Array(PACKAGE_ATTRS),
            "scope": "available",
            "patterns": dbus.Array([package_name]),
            "latest-limit": 10,
            "with_src": False,
        }
        logger.debug(f"Options: {options}")
        res = iface_rpm.list(options)
        if res is None:
            logger.error("No packages found")
            return []
        pkgs = get_yumex_packages(res)
        return pkgs
    except dbus.DBusException as e:
        logger.error(e)
        return []


def get_repo_priorities(session) -> list:
    """Get a list of repositories"""
    try:
        iface_repo = dbus.Interface(SYSTEM_BUS.get_object(DNFDAEMON_BUS_NAME, session), dbus_interface=IFACE_REPO)
        repos = iface_repo.list(
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


def get_yumex_packages(pkgs: list) -> list:
    """Convert a list of packages to YumexPackage objects"""
    yumex_pkgs = [create_package(pkg) for pkg in pkgs]
    return yumex_pkgs


def check_dnf_updates(refresh: bool = False) -> list:
    session = open_session()
    try:
        if session:
            options = {
                "package_attrs": dbus.Array(PACKAGE_ATTRS),
                "scope": "upgrades",
                "patterns": dbus.Array(["*"]),
                "latest-limit": 1,
            }
            iface_rpm = dbus.Interface(SYSTEM_BUS.get_object(DNFDAEMON_BUS_NAME, session), dbus_interface=IFACE_RPM)
            pkgs = get_yumex_packages(iface_rpm.list(options))
            repo_priorities = get_repo_priorities(session)
            packages_by_name = partial(get_packages_by_name, session)
            updates = FilterUpdates(repo_priorities, packages_by_name).get_updates(pkgs)
            close_session(session)
            return updates
    except dbus.DBusException as e:
        logger.error(e)
    return []


if __name__ == "__main__":
    print(len(check_dnf_updates()))
