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

from dataclasses import dataclass, field
from dnfdaemon.client import Client, DaemonError
from yumex.backend.dnf import YumexPackage

from yumex.ui.progress import YumexProgress
from yumex.utils import log
from yumex.utils.enums import PackageState


@dataclass
class Result:
    """Result from a dnfdaemon transaction
    contains a state of the transaction and the the data
    """

    completed: bool
    data: list = field(default_factory=list)


@dataclass
class TransactionResult:
    """transaction result object
    contains a state of the transaction and the the data
    or an error string is transaction failed
    """

    completed: bool
    data: dict = field(default_factory=dict)
    error: str = ""


class YumexRootBackend(Client):
    def __init__(self, progress) -> None:
        super().__init__()
        self.progress: YumexProgress = progress
        self.dnl_frac = 0.0

    def on_TransactionEvent(self, event, data) -> None:
        # Do your stuff here
        match event:
            case "start-build":
                self.progress.show()
                self.progress.set_title(_("Building Transaction"))
            case "end-build":
                self.progress.hide()
            case "start-run":
                self.progress.show()
                self.progress.set_title(_("Running Transaction"))
            case "run-transaction":
                self.progress.set_title(_("Applying Transaction"))
            case "end-run":
                self.progress.hide()
            case "signature-check":
                self.progress.set_title(_("Checking package signatures"))
            case "download":
                self.progress.set_title(_("Download Packages"))
            case "pkg-to-download":
                self.progress.set_title(_("Download Packages"))
            case _:
                log(f" --> on_TransactionEvent : {event} : {data}")

    def on_RPMProgress(
        self, package, action, te_current, te_total, ts_current, ts_total
    ):
        pkg_name, repo = self.id_to_nevra(package)
        match action:
            case "erase":
                self.progress.set_subtitle(_(f"Erasing : {pkg_name}"))
            case "install":
                self.progress.set_subtitle(_(f"Installing : {pkg_name}"))
            case "update":
                self.progress.set_subtitle(_(f"Updating : {pkg_name}"))
            case "updated":  # removing old package with being update
                pass
            case "verify":
                self.progress.set_subtitle(_(f"Verifying : {pkg_name}"))
            case "scriptlet":
                self.progress.set_subtitle(_(f"Running scriptlets : {pkg_name}"))
            case _:
                log(f" --> on_RPMProgress : {package} : {action}")

    def on_GPGImport(self, pkg_id, userid, hexkeyid, keyurl, timestamp) -> None:
        # TODO: Handle GPG key inport verification
        pass

    def on_DownloadStart(self, num_files, num_bytes) -> None:
        """Starting a new parallel download batch"""
        self.progress.set_title(_("Downloading Packages"))

    def on_DownloadProgress(self, name, frac, total_frac, total_files) -> None:
        """Progress for a single instance in the batch"""
        if total_frac - self.dnl_frac > 0.01:
            self.dnl_frac = total_frac
            self.progress.set_subtitle(_(f"Downloading : {name}"))
            self.progress.set_progress(total_frac)

    def on_DownloadEnd(self, name, status, msg) -> None:
        """Download of af single instace ended"""
        pass

    def on_RepoMetaDataProgress(self, name, frac) -> None:
        """Repository Metadata Download progress"""
        log(f" --> on_RepoMetaDataProgress : {name} : {frac}")

    def lock(self) -> None:
        self.Lock()

    def unlock(self) -> None:
        self.Unlock()

    def build_transaction(self, pkgs: list[YumexPackage]) -> TransactionResult:
        try:
            if self.Lock():
                self.ClearTransaction()
                for pkg in pkgs:
                    result: PackageState
                    match pkg.state:
                        case PackageState.AVAILABLE:
                            result = Result(*self.AddTransaction(pkg.id, "install"))
                        case PackageState.UPDATE:
                            result = Result(*self.AddTransaction(pkg.id, "update"))
                        case _:  # PackageState.INSTALLED
                            result = Result(*self.AddTransaction(pkg.id, "remove"))
                    if not result.completed:
                        log(f" --> RootBackendError : {result.data[0]}")
                result = Result(*self.BuildTransaction())
                if result.completed:
                    return TransactionResult(True, data=self.build_result(result.data))
                else:
                    log(" --> RootBackendError : BuildTransaction failled ")
                    return TransactionResult(
                        False,
                        error=_("Couldn't build transaction\n")
                        + "\n".join(result.data),
                    )
            else:
                log(" --> RootBackendError : can't get lock ")
                return TransactionResult(
                    False, error=_("Dnf is locked by another process")
                )
        except DaemonError as e:
            self.Unlock()
            return TransactionResult(
                False, error=_("Exception in Dnf Backend\n") + e.message
            )

    def build_result(self, result: list[str, list]) -> dict:
        result_dict = {}
        for action, pkgs in result:
            result_dict[action] = [
                (self.id_to_nevra(id), size) for id, size, extra in pkgs
            ]
        return result_dict

    def run_transaction(self, confirm) -> TransactionResult:
        try:
            if confirm:
                rc, msgs = self.RunTransaction()
                self.Unlock()
                if rc == 0:
                    return TransactionResult(True, data={"msgs": msgs})
                else:
                    return TransactionResult(False, error="\n".join(msgs))
            else:
                self.ClearTransaction()
                self.Unlock()
                return TransactionResult(
                    False, error=_("Transaction cancelled by user")
                )
        except DaemonError as e:
            self.Unlock()
            return TransactionResult(
                False, error=_("Exception in Dnf Backend : ") + str(e.message)
            )

    @staticmethod
    def id_to_nevra(id) -> tuple[str, str]:
        n, e, v, r, a, repo = id.split(",")
        if e != "0":
            return f"{n}-{e}:{v}-{r}.{a}", repo
        else:
            return f"{n}-{v}-{r}.{a}", repo
