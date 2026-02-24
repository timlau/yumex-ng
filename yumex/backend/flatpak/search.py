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

"""Backend for searching in flatpak AppStream Metadata"""
from typing import Optional

import logging
from enum import IntEnum
from pathlib import Path

import gi

gi.require_version("AppStream", "1.0")
gi.require_version("Flatpak", "1.0")

from gi.repository import AppStream, Flatpak, Gio, GLib

logger = logging.getLogger(__name__)


class Match(IntEnum):
    NAME = 1
    ID = 2
    SUMMARY = 3
    NONE = 4


class AppStreamPackage:
    """AppStream Package"""

    def __init__(self, comp: AppStream.Component, repo_name) -> None:
        self.component: AppStream.Component = comp
        self.repo_name: str = repo_name
        bundle: Optional[ AppStream.Bundle] = comp.get_bundle(AppStream.BundleKind.FLATPAK)
        self.flatpak_bundle: str = bundle.get_id() if bundle else ""
        self.match = Match.NONE

    @property
    def id(self) -> str:
        return self.component.get_id()

    @property
    def flatpak_id(self) -> str:
        return self.flatpak_bundle.split("/")[1]

    @property
    def name(self) -> str:
        return self.component.get_name()

    @property
    def summary(self) -> str:
        return self.component.get_summary()

    @property
    def version(self) -> Optional[str]:
        releases = self.component.get_releases_plain()  # ty:ignore[unresolved-attribute]
        if releases:
            release = releases.index_safe(0)
            if release:
                version = release.get_version()
                return version
        return None

    @property
    def developer(self) -> Optional[str]:
        developer = str(self.component.get_developer().get_name())  # ty:ignore[unresolved-attribute]
        return GLib.markup_escape_text(developer) if developer else None

    def __str__(self) -> str:
        return f"{self.name} - {self.summary} ({self.flatpak_bundle})"

    def search(self, keyword):
        if keyword in self.name.lower():
            return Match.NAME
        elif keyword in self.id.lower():
            return Match.ID
        elif keyword in self.summary.lower():
            return Match.SUMMARY
        else:
            return Match.NONE


class AppstreamSearcher:
    """Flatpak AppStream Package seacher"""

    def __init__(self) -> None:
        self.remotes: dict[str, list[AppStreamPackage]] = {}
        self.installed = []

    def add_installation(self, inst: Flatpak.Installation):
        """Add enabled flatpak repositories from Flatpak.Installation"""
        remotes = inst.list_remotes()
        for remote in remotes:
            if not remote.get_disabled():
                self.add_remote(remote, inst)

    def add_remote(self, remote: Flatpak.Remote, inst: Flatpak.Installation):
        """Add packages for a given Flatpak.Remote"""
        remote_name = remote.get_name()
        self.installed.extend([ref.format_ref() for ref in inst.list_installed_refs_by_kind(Flatpak.RefKind.APP)])
        if remote_name not in self.remotes:
            self.remotes[remote_name] = self._load_appstream_metadata(remote)

    def _load_appstream_metadata(self, remote: Flatpak.Remote) -> list[AppStreamPackage]:
        """load AppStrean metadata and create AppStreamPackage objects"""
        packages = []
        metadata = AppStream.Metadata.new()
        metadata.set_format_style(AppStream.FormatStyle.CATALOG)
        appstream_file = Path(remote.get_appstream_dir().get_path() + "/appstream.xml.gz")  # ty:ignore[unsupported-operator]
        if appstream_file.exists():
            metadata.parse_file(Gio.File.new_for_path(appstream_file.as_posix()), AppStream.FormatKind.XML)
            components: AppStream.ComponentBox = metadata.get_components()  # ty:ignore[unresolved-attribute]
            i = 0
            for i in range(components.get_size()):  # ty:ignore[unresolved-attribute]
                component = components.index_safe(i)  # ty:ignore[unresolved-attribute]
                if component.get_kind() == AppStream.ComponentKind.DESKTOP_APP:
                    bundle = component.get_bundle(AppStream.BundleKind.FLATPAK).get_id()
                    if bundle not in self.installed:
                        packages.append(AppStreamPackage(component, remote.get_name()))
            return packages
        else:
            logger.debug(f"AppStream file not found: {appstream_file}")
            return []

    def search(self, keyword: str) -> list[AppStreamPackage]:
        """Search packages matching a keyword"""
        search_results = []
        keyword = keyword.lower()
        for remote_name in self.remotes.keys():
            packages = self.remotes[remote_name]
            for package in packages:
                found = package.search(keyword)
                if found != Match.NONE:
                    logger.debug(f" found : {package} match: {found}")
                    package.match = found
                    search_results.append(package)
        return sorted(search_results, key=lambda pkg: (pkg.match, pkg.name))
