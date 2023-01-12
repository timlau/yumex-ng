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

from yumex.utils import log
from yumex.utils.types import FlatpakRefString
from yumex.utils.enums import FlatpakAction, FlatpakLocation


class FlatPakFirstRun(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class FlatpakTransaction:
    def __init__(self, backend, system: FlatpakLocation, first_run: bool = False):
        self.win = backend.win
        self.backend = backend
        self.first_run = first_run
        self._current_result = None
        if system is FlatpakLocation.SYSTEM:
            log(" FlatpakTransaction: setup system transaction")
            self.transaction = Flatpak.Transaction.new_for_installation(
                self.backend.system
            )
        else:
            log(" FlatpakTransaction: setup user transaction")
            self.transaction = Flatpak.Transaction.new_for_installation(
                self.backend.user
            )
        self.num_actions = 0
        self.current_action = 0
        self.transaction.connect("ready", self.on_ready)
        self.transaction.connect("new-operation", self.on_new_operation)
        self.transaction.connect("operation-done", self.operation_done)

    def _parse_operation(self, opration_type: Flatpak.TransactionOperationType) -> str:
        match opration_type.get_operation_type():
            case Flatpak.TransactionOperationType.INSTALL:
                return _("Installing")
            case Flatpak.TransactionOperationType.UNINSTALL:
                return _("Uninstalling")
            case Flatpak.TransactionOperationType.UPDATE:
                return _("Updating")
            case _:
                return ""

    def on_ready(self, transaction: Flatpak.Transaction) -> bool:
        """signal handler for FlatPak.Transaction::ready"""
        log(" FlatpakTransaction: ready")
        self.num_actions = len(transaction.get_operations())
        self.current_action = 0
        self.elem_progress = 1.0 / self.num_actions
        if self.first_run:
            self._current_result = transaction.get_operations()
            return False
        else:
            return True

    def on_changed(self, progress: Flatpak.TransactionProgress):
        """signal handler for FlatPak.TransactionProgress::changed"""
        cur_progress = progress.get_progress()
        total_progress = (self.current_action - 1) * self.elem_progress + (
            (cur_progress / 100.0) * self.elem_progress
        )
        self.win.progress.set_progress(total_progress)

    def on_new_operation(self, transaction, operation, progress) -> None:
        """signal handler for FlatPak.Transaction::new-operation"""
        log(" FlatpakTransaction: new-operation")
        self.current_action += 1
        progress.connect("changed", self.on_changed)
        ref = operation.get_ref()
        operation_type = self._parse_operation(operation)
        msg = f"{operation_type} {ref}"
        self.win.progress.set_subtitle(msg)
        log(f" FlatpakTransaction: {msg}")

    def operation_done(self, transaction, operation, commit, result) -> None:
        """signal handler for FlatPak.Transaction::operation-done"""
        log(" FlatpakTransaction: operation-done")
        if self.current_action == self.num_actions:
            log(" FlatpakTransaction: everyting is Done")

    def add_install(self, to_inst: FlatpakRefString, source: str) -> None:
        """add ref sting to transaction for install"""
        log(f" FlatpakTransaction: adding {to_inst} for install")
        self.transaction.add_install(source, to_inst, None)

    def add_remove(self, to_remove: FlatpakRefString) -> None:
        """add ref sting to transaction for uninstall"""
        log(f" FlatpakTransaction: adding {to_remove} for uninstall")
        self.transaction.add_uninstall(to_remove)

    def add_update(self, pkg: FlatpakPackage) -> None:
        """add pkg to transaction for update"""
        log(f" FlatpakTransaction: adding {pkg.id} for update")
        self.transaction.add_update(pkg.ref.format_ref(), None, None)

    def run(self) -> bool:
        """run the tranaction"""
        log(" FlatpakTransaction: Running Transaction")
        try:
            self.transaction.run()
        except GLib.GError as e:  # type: ignore
            msg = e.message
            if msg == "Aborted by user" and self.first_run:
                log(" FlatpakTransaction: First run, validate results")
                raise FlatPakFirstRun
            else:
                log(msg)
                self.win.show_message(f"{msg}", timeout=5)
                return False
        log(" FlatpakTransaction: Running Transaction Ended")
        return True

    def populate(
        self, pkgs: list[FlatpakPackage], action: FlatpakAction, source: str | None
    ):
        for pkg in pkgs:
            match action:
                case FlatpakAction.UPDATE:
                    self.add_update(pkg)
                case FlatpakAction.INSTALL:
                    self.add_install(pkg, source)
                case FlatpakAction.UNINSTALL:
                    self.add_remove(repr(pkg))
