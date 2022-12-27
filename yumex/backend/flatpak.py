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
# Copyright (C) 2022  Tim Lauridsen
#

""" backend for handling flatpak"""
import gi

gi.require_version("Flatpak", "1.0")

from enum import IntEnum  # noqa : E402
from gi.repository import Flatpak, GObject  # noqa : E402

from yumex.utils import log  # noqa : E402


class FlatpakType(IntEnum):
    APP = 1
    RUNTIME = 2
    LOCALE = 3
    DEBUG = 4


class FlatpakPackage(GObject.GObject):
    """wrapper for a"""

    def __init__(self, ref, is_user=True, is_update=False):
        super(FlatpakPackage, self).__init__()
        self.ref = ref
        self.is_user = is_user
        self.is_update = is_update

    @property
    def name(self):
        return self.ref.get_appdata_name()

    @property
    def location(self):
        if self.is_user:
            return "user"
        else:
            return "system"

    @property
    def version(self):
        return self.ref.get_appdata_version()

    @property
    def summary(self):
        return self.ref.get_appdata_summary()

    @property
    def origin(self):
        return self.ref.get_origin()

    @property
    def id(self):
        return self.ref.get_name()

    @property
    def type(self):
        ref_kind = self.ref.get_kind()
        match ref_kind:
            case Flatpak.RefKind.APP:
                pak_type = FlatpakType.APP
            case Flatpak.RefKind.RUNTIME:
                pak_type = FlatpakType.RUNTIME
                if self.id.endswith(".Locale"):
                    pak_type = FlatpakType.LOCALE
        return pak_type

    def __repr__(self) -> str:
        return self.ref.format_ref()


class FlatpakTransaction:
    def __init__(self, backend, system=True):
        self.win = backend.win
        self.backend = backend
        if system:
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

    def on_ready(self, transaction):
        log(" FLATPAK: ready")
        self.num_actions = len(transaction.get_operations())
        self.current_action = 0
        self.elem_progress = 1.0 / self.num_actions
        return True

    def on_changed(self, progress):
        cur_progress = progress.get_progress()
        total_progress = (self.current_action - 1) * self.elem_progress + (
            (cur_progress / 100.0) * self.elem_progress
        )
        self.win.progress.set_progress(total_progress)

    def on_new_operation(self, transaction, operation, progress):
        log(" FLATPAK: new-operation")
        self.current_action += 1
        progress.connect("changed", self.on_changed)
        ref = operation.get_ref()
        self.win.progress.set_subtitle(ref)
        log(f" FLATPAK: {ref}")

    def operation_done(self, transaction, operation, commit, result):
        log(" FLATPAK: operation-done")
        if self.current_action == self.num_actions:
            log(" FLATPAK: everyting is Done")

    def add_install(self, to_inst, source):
        self.transaction.add_install(source, to_inst, None)
        log(f" FLATPAK: adding {to_inst} for install")

    def add_remove(self, to_remove):
        self.transaction.add_uninstall(to_remove)
        log(f" FLATPAK: adding {to_remove} for uninstall")

    def add_update(self, pkg):
        self.transaction.add_update(pkg.ref.format_ref(), None, None)
        log(f" FLATPAK: adding {pkg.id} for update")

    def run(self):
        log(" FLATPAK: Running Transaction")
        self.win.progress.show()
        self.win.progress.set_title(_("Running Flatpak Transaction"))
        self.transaction.run()
        log(" FLATPAK: Running Transaction Ended")


class FlatpakBackend:
    def __init__(self, win):
        self.win = win
        self.user = Flatpak.Installation.new_user()
        self.system = Flatpak.Installation.new_system()
        self.updates = self._get_updates()

    def find(self, source, key):
        refs = self.user.list_remote_refs_sync(source)
        for ref in refs:
            if ref.get_kind() == Flatpak.RefKind.APP:
                if key in ref.get_name():
                    return ref.get_name()
        return None

    def find_ref(self, source, key):
        refs = self.user.list_remote_refs_sync(source)
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

    def get_remotes(self, system=False):
        if system:
            return sorted([remote.get_name() for remote in self.system.list_remotes()])
        else:
            return sorted([remote.get_name() for remote in self.user.list_remotes()])

    def get_arch(self):
        return Flatpak.get_default_arch()

    def _get_updates(self):
        updates = [ref.get_name() for ref in self.user.list_installed_refs_for_update()]
        updates += [
            ref.get_name() for ref in self.system.list_installed_refs_for_update()
        ]
        return updates

    def _get_package(self, ref, is_user=True):
        if ref.get_name() in self.updates:
            is_update = True
        else:
            is_update = False
        return FlatpakPackage(ref, is_user=is_user, is_update=is_update)

    def do_update(self, pkgs: list[FlatpakPackage]):
        transaction = FlatpakTransaction(self)
        for pkg in pkgs:
            if pkg.is_update:
                transaction.add_update(pkg)
                log(f" FLATPAK: adding {pkg.id} for update")
        transaction.run()

    def do_install(self, to_inst, source, location):
        if location == "user":
            transaction = FlatpakTransaction(self, system=False)
        else:
            transaction = FlatpakTransaction(self, system=True)
        try:
            transaction.add_install(to_inst, source)
            return transaction.run()
        except Exception as e:
            log(str(e))
            msg = str(e).split(":")[-1]
            self.win.show_message(f"{msg}", timeout=5)
            return False

    def do_remove(self, pkg: FlatpakPackage):
        if pkg.location == "user":
            transaction = FlatpakTransaction(self, system=False)
        else:
            transaction = FlatpakTransaction(self, system=True)
        to_remove = repr(pkg)
        try:
            transaction.add_remove(to_remove)
            return transaction.run()
        except Exception as e:
            log(str(e))
            msg = str(e).split(":")[-1]
            self.win.show_message(f"{msg}", timeout=5)
            return False

    def get_installed(self, user=True, system=True):
        refs = []
        if user:
            refs += [self._get_package(ref) for ref in self.user.list_installed_refs()]
        if system:
            refs += [
                self._get_package(ref, is_user=False)
                for ref in self.system.list_installed_refs()
            ]
        return refs
