import logging

import dbus

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


# import logging
# from pathlib import Path

# import libdnf5 as dnf
# from libdnf5.common import QueryCmp_NEQ
# from libdnf5.repo import RepoCache, RepoQuery  # noqa: F401
# from libdnf5.rpm import Package, PackageQuery  # noqa: F401

# logger = logging.getLogger(__name__)


# def get_repo_priority(base: dnf.base.Base, repo_name: str) -> int:
#     repos_query = RepoQuery(base)
#     for repo in repos_query:
#         if repo.get_id() == repo_name:
#             return repo.get_priority()
#     return 99


# def get_package_repos(base: dnf.base.Base, package_name: str) -> list[str]:
#     repos = set()
#     query = PackageQuery(base)
#     query.filter_name([package_name])
#     for pkg in query:
#         repos.add(pkg.get_repo_id())
#     return list(repos)


# def get_prioritied_packages(updates: list[Package], base):
#     """Get Prioritized version of updates"""
#     latest_versions = {}
#     for pkg in updates:
#         repos = get_package_repos(base, pkg.get_name())
#         repo_priorities = [get_repo_priority(base, repo) for repo in repos]
#         lowest_priority = min(repo_priorities) if repo_priorities else 99
#         pkg_repo_priority = get_repo_priority(base, pkg.get_repo_id())

#         if pkg_repo_priority == lowest_priority:
#             if pkg.get_name() in latest_versions:
#                 if pkg.get_evr() > latest_versions[pkg.get_name()].get_evr():
#                     latest_versions[pkg.get_name()] = pkg
#             else:
#                 latest_versions[pkg.get_name()] = pkg

#     return list(latest_versions.values())


# def expire_metadata(base: dnf.base.Base, cachedir):
#     # get the repo cache dir
#     cachedir = Path(cachedir)
#     # interate through the repo cachedir
#     for fn in cachedir.iterdir():
#         if not fn.is_dir():
#             continue
#         # Setup a RepoCache at the current repo cachedir
#         repo_cache = RepoCache(base, fn.as_posix())
#         # expire the cache for the current repo
#         repo_cache.write_attribute(RepoCache.ATTRIBUTE_EXPIRED)


def check_dnf_updates(refresh: bool = False) -> list:
    bus = dbus.SystemBus()

    # open a new session with dnf5daemon-server
    iface_session = dbus.Interface(
        bus.get_object(DNFDAEMON_BUS_NAME, DNFDAEMON_OBJECT_PATH),
        dbus_interface=IFACE_SESSION_MANAGER,
    )
    session = iface_session.open_session(dbus.Dictionary({}, signature=dbus.Signature("sv")))

    options = {
        # retrieve all package attributes
        "package_attrs": [
            "repo_id",
            "full_nevra",
        ],
        # take all packages into account (other supported scopes are installed, available,
        # upgrades, upgradable)
        "scope": "upgrades",
        # get only packages with name starting with "a"
        "patterns": ["*"],
        # return only the latest version for each name.arch
        "latest-limit": 1,
    }
    iface_rpm = dbus.Interface(bus.get_object(DNFDAEMON_BUS_NAME, session), dbus_interface=IFACE_RPM)
    pkgs = iface_rpm.list(options)
    iface_session.close_session(session)
    return pkgs


if __name__ == "__main__":
    print(len(check_dnf_updates()))
