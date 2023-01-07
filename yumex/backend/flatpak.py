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

from enum import IntEnum, StrEnum, auto
from gi.repository import Flatpak, GObject, GLib


from yumex.utils import log

from yumex.utils.types import FlatpakRefString, FlatpakRef, MainWindow


class FlatpakType(IntEnum):
    """flatpak type"""

    APP = 1
    RUNTIME = 2
    LOCALE = 3
    DEBUG = 4


class FlatpakLocation(StrEnum):
    """flatpak install location"""

    USER = auto()
    SYSTEM = auto()
    BOTH = auto()  # used only as a filter, where we want both locations


class FlatpakPackage(GObject.GObject):
    """wrapper for a installed flatpak"""

    def __init__(self, ref: FlatpakRef, location: FlatpakLocation, is_update=False):
        super().__init__()
        self.ref: FlatpakRef = ref
        self.is_update = is_update
        self.location = location

    @property
    def is_user(self) -> bool:
        """return if the flatpak is installed in user context"""
        return self.location == FlatpakLocation.USER

    @property
    def name(self) -> str:
        """return the application name (not id) : ex. Contrast"""
        return self.ref.get_appdata_name()

    @property
    def version(self) -> str:
        """return the flatpak version"""
        return self.ref.get_appdata_version()

    @property
    def summary(self) -> str:
        """return the flatpak summary"""
        return self.ref.get_appdata_summary()

    @property
    def origin(self) -> str:
        """return the origin remote"""
        return self.ref.get_origin()

    @property
    def id(self) -> str:
        """return the name/id: ex. org.gnome.design.Contrast"""
        return self.ref.get_name()

    @property
    def type(self) -> FlatpakType:
        """the ref type as Enum (runtime/app/locale)"""
        ref_kind = self.ref.get_kind()
        pak_type = FlatpakType.APP
        match ref_kind:
            case Flatpak.RefKind.RUNTIME:
                pak_type = FlatpakType.RUNTIME
                if self.id.endswith(".Locale"):
                    pak_type = FlatpakType.LOCALE
        return pak_type

    def __repr__(self) -> FlatpakRefString:
        """return the ref as string: ex. app/org.gnome.design.Contrast/x86_64/stable"""
        return self.ref.format_ref()


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

    def do_update_all(self, pkgs: list[FlatpakPackage]) -> None:
        """update all flatpaks with available updates"""
        user_updates = [pkg for pkg in pkgs if pkg.is_update and pkg.is_user]
        system_updates = [pkg for pkg in pkgs if pkg.is_update and not pkg.is_user]
        if user_updates:
            transaction = FlatpakTransaction(self, system=False)
            for pkg in user_updates:
                transaction.add_update(pkg)
            transaction.run()
        if system_updates:
            transaction = FlatpakTransaction(self, system=True)
            for pkg in system_updates:
                transaction.add_update(pkg)
            transaction.run()

    def do_install(self, to_inst, source, location: FlatpakLocation) -> None:
        """install a flatak by a ref string"""
        transaction = FlatpakTransaction(self, system=location)
        try:
            transaction.add_install(to_inst, source)
            return transaction.run()
        except GLib.GError as e:  # type: ignore
            msg = e.message
            log(msg)
            self.win.show_message(f"{msg}", timeout=5)
            return False

    def do_remove(self, pkg: FlatpakPackage) -> None:
        """uninstall a flatpak pkg"""
        transaction = FlatpakTransaction(self, system=pkg.location)
        to_remove = repr(pkg)
        try:
            transaction.add_remove(to_remove)
            return transaction.run()
        except GLib.GError as e:  # type: ignore
            msg = e.message
            log(msg)
            self.win.show_message(f"{msg}", timeout=5)
            return False

    def do_update(self, pkg: FlatpakPackage) -> None:
        """update a flatpak pkg"""
        transaction = FlatpakTransaction(self, system=pkg.location)
        try:
            transaction.add_update(pkg)
            return transaction.run()
        except GLib.GError as e:  # type: ignore
            msg = e.message
            log(msg)
            self.win.show_message(f"{msg}", timeout=5)
            return False

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


class FlatpakTransaction:
    def __init__(self, backend: FlatpakBackend, system: FlatpakLocation):
        self.win = backend.win
        self.backend = backend
        if system is FlatpakLocation.SYSTEM:
            log(" FLATPAK: setup system transaction")
            self.transaction = Flatpak.Transaction.new_for_installation(
                self.backend.system
            )
        else:
            log(" FLATPAK: setup user transaction")
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
        log(" FLATPAK: ready")
        self.num_actions = len(transaction.get_operations())
        self.current_action = 0
        self.elem_progress = 1.0 / self.num_actions
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
        log(" FLATPAK: new-operation")
        self.current_action += 1
        progress.connect("changed", self.on_changed)
        ref = operation.get_ref()
        operation_type = self._parse_operation(operation)
        msg = f"{operation_type} {ref}"
        self.win.progress.set_subtitle(msg)
        log(f" FLATPAK: {msg}")

    def operation_done(self, transaction, operation, commit, result) -> None:
        """signal handler for FlatPak.Transaction::operation-done"""
        log(" FLATPAK: operation-done")
        if self.current_action == self.num_actions:
            log(" FLATPAK: everyting is Done")

    def add_install(self, to_inst: FlatpakRefString, source: str) -> None:
        """add ref sting to transaction for install"""
        log(f" FLATPAK: adding {to_inst} for install")
        self.transaction.add_install(source, to_inst, None)

    def add_remove(self, to_remove: FlatpakRefString) -> None:
        """add ref sting to transaction for uninstall"""
        log(f" FLATPAK: adding {to_remove} for uninstall")
        self.transaction.add_uninstall(to_remove)

    def add_update(self, pkg: FlatpakPackage) -> None:
        """add pkg to transaction for update"""
        log(f" FLATPAK: adding {pkg.id} for update")
        self.transaction.add_update(pkg.ref.format_ref(), None, None)

    def run(self) -> None:
        """run the tranaction"""
        log(" FLATPAK: Running Transaction")
        self.win.progress.show()
        self.win.progress.set_title(_("Running Flatpak Transaction"))
        self.transaction.run()
        log(" FLATPAK: Running Transaction Ended")
