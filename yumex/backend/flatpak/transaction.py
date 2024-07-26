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

"""backend for handling flatpaks"""

from pathlib import Path
from gi.repository import Flatpak, GLib
from yumex.backend.flatpak import FlatpakPackage, FlatpakUpdate

from yumex.utils import log
from yumex.utils.types import FlatpakRefString
from yumex.utils.enums import FlatpakAction, FlatpakLocation


class FlatPakFirstRun(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class FlatPakNoOperations(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class FlatpakTransaction:
    def __init__(self, backend, location: FlatpakLocation, first_run: bool = False):
        self.win = backend.win
        self.backend = backend
        self.first_run = first_run
        self._current_result = None
        self.failed = False
        self.failed_msg = None
        if location is FlatpakLocation.SYSTEM:
            log(" FlatpakTransaction: setup system transaction")
            self.transaction = Flatpak.Transaction.new_for_installation(self.backend.system)
        else:
            log(" FlatpakTransaction: setup user transaction")
            self.transaction = Flatpak.Transaction.new_for_installation(self.backend.user)
        self.num_actions = 0
        self.current_action = 0
        self.transaction.connect("ready", self.on_ready)
        self.transaction.connect("new-operation", self.on_new_operation)
        self.transaction.connect("operation-done", self.operation_done)
        self.transaction.connect("operation-error", self.operation_error)
        self.transaction.connect("end-of-lifed", self.operation_eol)
        self.transaction.connect("end-of-lifed-with-rebase", self.operation_eol_rebase)

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
        if not self.num_actions:
            log(" FlatpakTransaction: nothing to do")
            self.failed = True
            self.failed_msg = "nothing to do"
            return True
            # raise FlatPakNoOperations("FlatpakTransaction: no operations")
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
        total_progress = (self.current_action - 1) * self.elem_progress + ((cur_progress / 100.0) * self.elem_progress)
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

    def operation_eol(self, transaction, ref, reason, rebase) -> None:
        """signal handler for FlatPak.Transaction::end-of-lifed"""
        log(" FlatpakTransaction: end-of-lifed")
        log(f" FlatpakTransaction: --> {ref}")
        log(f" FlatpakTransaction: --> {reason}")
        log(f" FlatpakTransaction: --> {rebase}")

    def operation_eol_rebase(self, transaction, remote, ref, reason, rebase, prev_ids) -> None:
        """signal handler for FlatPak.Transaction::end-of-lifed-with-rebase"""
        log(" FlatpakTransaction: end-of-lifed-with-rebase")
        log(f" FlatpakTransaction: --> {ref}")
        log(f" FlatpakTransaction: --> {reason}")
        log(f" FlatpakTransaction: --> {rebase}")
        log(f" FlatpakTransaction: --> {prev_ids}")

    def operation_error(self, transaction, operation, error, result) -> None:
        """signal handler for FlatPak.Transaction::operation-error"""
        log(" FlatpakTransaction: operation-error")
        log(f" FlatpakTransaction:  --> {str(error)}")

    def add_install(self, to_inst: FlatpakRefString, source: str) -> None:
        """add ref sting to transaction for install"""
        log(f" FlatpakTransaction: adding {to_inst} for install")
        self.transaction.add_install(source, to_inst, None)

    def add_install_flatpak_ref(self, flatpak_ref: Path) -> None:
        """add flatpakref to transaction for install"""
        log(f" FlatpakTransaction: adding flatpakref {flatpak_ref} for install")
        ref_bytes = flatpak_ref.read_bytes()
        gl_bytes = GLib.Bytes.new(ref_bytes)
        self.transaction.add_install_flatpakref(gl_bytes)

    def add_remove(self, to_remove: FlatpakRefString) -> None:
        """add ref sting to transaction for uninstall"""
        log(f" FlatpakTransaction: adding {to_remove} for uninstall")
        self.transaction.add_uninstall(to_remove)

    def add_update(self, pkg: FlatpakPackage) -> None:
        """add pkg to transaction for update"""
        if pkg.is_update == FlatpakUpdate.UPDATE:
            self.transaction.add_update(pkg.ref.format_ref(), None, None)
            log(f" FlatpakTransaction: adding {pkg.id} for update")
        elif pkg.is_update == FlatpakUpdate.EOL:
            rebase_ref = pkg.ref.get_eol_rebase()
            log(f" FlatpakTransaction: adding {pkg.id} for rebase")
            log(f" flatpak: rebase {pkg.ref.format_ref()} -> {rebase_ref}")
            # rebase to new version
            if rebase_ref:
                self.transacton.add_rebase(pkg.origin, rebase_ref, None, [pkg.ref.get_name()])
                self.add_remove(str(pkg))  # remove the old version

    def run(self) -> bool:
        """run the tranaction"""
        log(" FlatpakTransaction: Running Transaction")
        try:
            self.transaction.run()
        except GLib.GError as e:  # type: ignore
            msg = e.message
            if self.first_run:
                log(f" FlatpakTransaction: First run, validate results : {msg}")
                raise FlatPakFirstRun
            else:
                log(msg)
                self.win.show_message(f"{msg}", timeout=2)
                return False
        if self.failed:
            log(f" FlatpakTransaction: Transaction Failed : {self.failed_msg}")
            msg = _("flatpak transaction failed") + f" : {self.failed_msg}"
            self.win.show_message(f"{msg}", timeout=5)
            return False
        log(" FlatpakTransaction: Running Transaction Ended")
        return True

    def populate(self, pkgs: list[FlatpakPackage], action: FlatpakAction, source: str | None):
        for pkg in pkgs:
            match action:
                case FlatpakAction.UPDATE:
                    self.add_update(pkg)
                case FlatpakAction.INSTALL:
                    self.add_install(pkg, source)
                case FlatpakAction.UNINSTALL:
                    self.add_remove(repr(pkg))
