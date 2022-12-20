from dnfdaemon.client import Client, DaemonError
from yumex.backend import PackageState, YumexPackage

from yumex.ui.progress import YumexProgress
from yumex.utils import log


class YumexRootBackend(Client):
    def __init__(self, progress):
        super(YumexRootBackend, self).__init__()
        self.progress: YumexProgress = progress
        self.dnl_frac = 0.0

    def on_TransactionEvent(self, event, data):
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

    def on_GPGImport(self, pkg_id, userid, hexkeyid, keyurl, timestamp):
        # do stuff here
        pass

    def on_DownloadStart(self, num_files, num_bytes):
        """Starting a new parallel download batch"""
        # do stuff here
        self.progress.set_title(_("Downloading Packages"))

    def on_DownloadProgress(self, name, frac, total_frac, total_files):
        """Progress for a single instance in the batch"""
        # do stuff here
        if total_frac - self.dnl_frac > 0.01:
            self.dnl_frac = total_frac
            self.progress.set_subtitle(_(f"Downloading : {name}"))
            self.progress.set_progress(total_frac)

    def on_DownloadEnd(self, name, status, msg):
        """Download of af single instace ended"""
        # do stuff here
        pass

    def on_RepoMetaDataProgress(self, name, frac):
        """Repository Metadata Download progress"""
        # do stuff here
        log(f" --> on_RepoMetaDataProgress : {name} : {frac}")

    def lock(self):
        self.Lock()

    def unlock(self):
        self.Unlock()

    def build_transaction(self, pkgs: list[YumexPackage]):
        try:
            if self.Lock():
                self.ClearTransaction()
                for pkg in pkgs:
                    match pkg.state:
                        case PackageState.AVAILABLE:
                            rc, err_msgs = self.AddTransaction(pkg.id, "install")
                        case PackageState.UPDATE:
                            rc, err_msgs = self.AddTransaction(pkg.id, "update")
                        case PackageState.INSTALLED:
                            rc, err_msgs = self.AddTransaction(pkg.id, "remove")
                    if not rc:
                        log(f" --> RootBackendError : {err_msgs[0]}")
                rc, result = self.BuildTransaction()
                if rc:
                    return True, self.build_result(result)
                else:
                    log(" --> RootBackendError : BuildTransaction failled ")
                    return False, {
                        "errors": _("Couldn't build transaction\n") + "\n".join(result)
                    }
            else:
                log(" --> RootBackendError : can't get lock ")
                return False, {"errors": _("Dnf is locked by another process")}
        except DaemonError as e:
            self.Unlock()
            return False, {"errors": _("Exception in Dnf Backend\n") + str(e)}

    def build_result(self, result):
        result_dict = {}
        for action, pkgs in result:
            result_dict[action] = [
                (self.id_to_nevra(id), size) for id, size, extra in pkgs
            ]
        return result_dict

    def run_transaction(self, confirm):
        try:
            if confirm:
                rc, msgs = self.RunTransaction()
                self.Unlock()
                if rc == 0:
                    return True, msgs
                else:
                    return False, msgs
            else:
                self.ClearTransaction()
                self.Unlock()
                return False, "transaction canceled"
        except DaemonError as e:
            self.Unlock()
            return False, _("Exception in Dnf Backend\n") + str(e)

    @staticmethod
    def id_to_nevra(id):
        n, e, v, r, a, repo = id.split(",")
        if e != "0":
            return f"{n}-{e}:{v}-{r}.{a}", repo
        else:
            return f"{n}-{v}-{r}.{a}", repo
