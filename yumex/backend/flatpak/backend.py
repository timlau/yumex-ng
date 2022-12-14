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
# Copyright (C) 2023  Tim Lauridsen

""" backend for handling flatpaks"""

from gi.repository import Flatpak, GLib
from yumex.backend.flatpak import FlatpakPackage
from yumex.backend.flatpak.transaction import FlatPakFirstRun, FlatpakTransaction

from yumex.utils import log
from yumex.utils.types import FlatpakRef, MainWindow
from yumex.utils.enums import FlatpakLocation, FlatpakAction


class FlatpakBackend:
    def __init__(self, win: MainWindow):
        self.win: MainWindow = win
        self.user: Flatpak.Installation = Flatpak.Installation.new_user()
        self.system: Flatpak.Installation = Flatpak.Installation.new_system()
        self.updates = self._get_updates()

    def find(self, source: str, key: str) -> str | None:
        """find an available id containing a key"""
        refs = self.user.list_remote_refs_sync(source)
        for ref in refs:
            if ref.get_kind() == Flatpak.RefKind.APP:
                if key.lower() in ref.get_name().lower():
                    return ref.get_name()
        return None

    def find_ref(self, source: str, key: str) -> str | None:
        """find the ref string containing a key"""
        refs: list[FlatpakRef] = self.user.list_remote_refs_sync(source)
        found = None
        for ref in refs:
            if ref.get_kind() == Flatpak.RefKind.APP:
                if key in ref.get_name():
                    found = ref
                    break
        if found:
            ref = f"app/{found.get_name()}/{found.get_arch()}/{found.get_branch()}"
            return ref
        return None

    def get_icon_path(self, remote_name: str) -> str | None:
        """get the path to flatpak icon cache"""
        remote = self.user.get_remote_by_name(remote_name)
        if remote:
            appstream_dir = remote.get_appstream_dir().get_path()
            return f"{appstream_dir}/icons/flatpak/128x128/"
        return None

    def get_remotes(self, location: FlatpakLocation) -> list[str]:
        """get a list of active flatpak remote names"""
        if location is FlatpakLocation.SYSTEM:
            return sorted([remote.get_name() for remote in self.system.list_remotes()])
        else:
            return sorted([remote.get_name() for remote in self.user.list_remotes()])

    def get_arch(self) -> str:
        """get the default arch"""
        return Flatpak.get_default_arch()

    def _get_updates(self) -> list[str]:
        """get a list of flatpak ids with available updates"""
        updates = [ref.get_name() for ref in self.user.list_installed_refs_for_update()]
        updates += [
            ref.get_name() for ref in self.system.list_installed_refs_for_update()
        ]
        return updates

    def _get_package(self, ref, location: FlatpakLocation) -> FlatpakPackage:
        """create a flatpak pkg object with update status"""
        if ref.get_name() in self.updates:
            is_update = True
        else:
            is_update = False
        return FlatpakPackage(ref, location=location, is_update=is_update)

    def _build_transaction(
        self, pkgs: list[FlatpakPackage], system: bool, action, **kwargs
    ) -> list[tuple[str, FlatpakAction, str]]:
        """run the transaction, ask user for confirmation and apply it"""
        source = kwargs.pop("source", None)
        transaction = FlatpakTransaction(self, system=system, first_run=True)
        for pkg in pkgs:
            match action:
                case FlatpakAction.UPDATE:
                    transaction.add_update(pkg)
                case FlatpakAction.INSTALL:
                    transaction.add_install(pkg, source)
                case FlatpakAction.UNINSTALL:
                    transaction.add_remove(pkg)
        try:
            transaction.run()
            return []
        except FlatPakFirstRun:
            result: list = transaction._current_result
            refs = [(oper.get_ref(), action, source) for oper in result]
            return refs

    def _execute_transaction(
        self, pkgs: list[FlatpakPackage], system: bool, action, **kwargs
    ):
        """run the transaction, ask user for confirmation and apply it"""
        source = kwargs.pop("source", None)
        transaction = FlatpakTransaction(self, system=system, first_run=False)
        for pkg in pkgs:
            match action:
                case FlatpakAction.UPDATE:
                    transaction.add_update(pkg)
                case FlatpakAction.INSTALL:
                    transaction.add_install(pkg, source)
                case FlatpakAction.UNINSTALL:
                    transaction.add_remove(pkg)
        transaction.run()

    def _do_transaction(
        self,
        user_pkgs: list[FlatpakPackage],
        system_pkgs: list[FlatpakPackage],
        action: FlatpakAction,
        execute=False,
        **kwargs,
    ) -> list[tuple[str, FlatpakAction, str]] | bool:
        try:
            refs_total = []
            if not execute:  # build the trasaction and return refs
                if user_pkgs:
                    refs = self._build_transaction(
                        user_pkgs, system=False, action=action, **kwargs
                    )
                    refs_total.extend(refs)
                if system_pkgs:
                    refs = self._build_transaction(
                        system_pkgs, system=True, action=action, **kwargs
                    )
                    refs_total.extend(refs)
                return refs_total
            else:  # execute the transaction
                if user_pkgs:
                    self._execute_transaction(
                        user_pkgs, system=False, action=action, **kwargs
                    )
                if system_pkgs:
                    self._execute_transaction(
                        system_pkgs, system=True, action=action, **kwargs
                    )
                return True

        except GLib.GError as e:  # type: ignore
            msg = e.message
            log(msg)
            self.win.show_message(f"{msg}", timeout=5)
            return False

    def do_update_all(self, pkgs: list[FlatpakPackage], execute) -> None:
        """update all flatpaks with available updates"""
        user_updates = [pkg for pkg in pkgs if pkg.is_update and pkg.is_user]
        system_updates = [pkg for pkg in pkgs if pkg.is_update and not pkg.is_user]
        return self._do_transaction(
            user_updates, system_updates, FlatpakAction.UPDATE, execute
        )

    def do_install(self, to_inst, source, location: FlatpakLocation, execute) -> None:
        """install a flatak by a ref string"""
        pkgs = [to_inst]
        if location == FlatpakLocation.USER:
            return self._do_transaction(
                pkgs, [], FlatpakAction.INSTALL, execute, source=source
            )
        else:
            return self._do_transaction(
                [], pkgs, FlatpakAction.INSTALL, execute, source=source
            )

    def do_remove(self, pkg: FlatpakPackage, execute: bool) -> None:
        """uninstall a flatpak pkg"""
        pkgs = [repr(pkg)]
        if pkg.location == FlatpakLocation.USER:
            return self._do_transaction(pkgs, [], FlatpakAction.UNINSTALL, execute)
        else:
            return self._do_transaction([], pkgs, FlatpakAction.UNINSTALL, execute)

    def do_update(self, pkg: FlatpakPackage, execute: bool) -> None:
        """update a flatpak pkg"""
        pkgs = [pkg]
        if pkg.location == FlatpakLocation.USER:
            return self._do_transaction(pkgs, [], FlatpakAction.UNINSTALL, execute)
        else:
            return self._do_transaction([], pkgs, FlatpakAction.UNINSTALL, execute)

    def get_installed(self, location: FlatpakLocation) -> list[FlatpakPackage]:
        """get list of installed flatpak pkgs"""
        refs = []
        if location in (FlatpakLocation.USER, FlatpakLocation.BOTH):
            refs += [
                self._get_package(ref, location=FlatpakLocation.USER)
                for ref in self.user.list_installed_refs()
            ]
        if location in (FlatpakLocation.SYSTEM, FlatpakLocation.BOTH):
            refs += [
                self._get_package(ref, location=FlatpakLocation.SYSTEM)
                for ref in self.system.list_installed_refs()
            ]
        return refs
