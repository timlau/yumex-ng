from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Self
from yumex.backend import TransactionResult
from yumex.backend.dnf import YumexPackage

from yumex.ui.progress import YumexProgress
from yumex.utils import log
from yumex.utils.enums import PackageState

from .client import Dnf5DbusClient, gv_list


class DownloadType(Enum):
    REPO = auto()
    PACKAGE = auto()
    UNKNOWN = auto()


@dataclass
class DownloadPackage:
    id: str
    name: str
    to_download: int
    downloaded: int = 0

    @property
    def package_type(self) -> DownloadType:
        prefix = self.id.split(":")[0]
        match prefix:
            case "repo":
                return DownloadType.REPO
            case "package":
                return DownloadType.PACKAGE
            case _:
                return DownloadType.UNKNOWN


@dataclass
class DownloadQueue:
    queue: dict[DownloadPackage] = field(default_factory=dict)

    @property
    def total(self):
        total = 0
        for pkg in self.queue.values():
            total += pkg.to_download
        return total

    @property
    def current(self):
        current = 0
        for pkg in self.queue.values():
            current += pkg.downloaded
        return current

    @property
    def fraction(self):
        if self.total:
            return float(self.current / self.total)
        else:
            return 0.0

    @property
    def is_completted(self):
        return self.current == self.total

    def add(self, pkg):
        self.queue[pkg.id] = pkg

    def clear(self):
        self.queue = {}

    def get(self, id):
        if id in self.queue:
            return self.queue[id]
        else:
            return None

    def __len__(self):
        return len(self.queue)


class YumexRootBackend:
    def __init__(self, presenter) -> None:
        super().__init__()
        self.presenter = presenter
        self.last_transaction = None
        self.download_queue = DownloadQueue()

    @property
    def progress(self) -> YumexProgress:
        return self.presenter.progress

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        ...

    def build_result(self, content: list) -> dict[str:list]:
        result_dict = {}
        for _, action, _, _, pkg in content:
            action = action.lower()
            if action not in result_dict:
                result_dict[action] = []
            name = pkg["name"].get_string()
            arch = pkg["arch"].get_string()
            evr = pkg["evr"].get_string()
            repo = pkg["repo_id"].get_string()
            if "package_size" in pkg:
                size = pkg["package_size"].get_uint64()
            elif "install_size" in pkg:
                size = pkg["install_size"].get_uint64()
            else:
                size = 0.0
                log("no size found : {pkg}")
            nevra = f"{name}-{evr}.{arch}"
            result_dict[action].append(((nevra, repo), size))
        return result_dict

    def _build_translations(self, pkgs: list[YumexPackage], client):
        to_install = []
        to_update = []
        to_remove = []
        for pkg in pkgs:
            match pkg.state:
                case PackageState.AVAILABLE:
                    log(f"DNF5_ROOT : adding {pkg.nevra} for install")
                    to_install.append(pkg.nevra)
                case PackageState.UPDATE:
                    log(f"DNF5_ROOT : adding {pkg.nevra} for update")
                    to_update.append(pkg.nevra)
                case PackageState.INSTALLED:
                    log(f"DNF5_ROOT : adding {pkg.nevra} for remove")
                    to_remove.append(pkg.nevra)
        if to_remove:
            client.session.remove(gv_list(to_remove), {})
        if to_install:
            client.session.install(gv_list(to_install), {})
        if to_update:
            client.session.upgrade(gv_list(to_update), {})
        res = client.resolve({})
        content, rc = res
        return content, rc

    def connect_signals(self, client):
        client.session.download_add_new.connect(self.on_download_add_new)
        client.session.download_progress.connect(self.on_download_progress)
        client.session.download_end.connect(self.on_download_end)
        client.session.repo_key_import_request.connect(self.on_repo_key_import_request)

    def build_transaction(self, pkgs: list[YumexPackage]) -> TransactionResult:
        self.last_transaction = pkgs
        with Dnf5DbusClient() as client:
            self.progress.show()
            self.progress.set_title(_("Building Transaction"))
            self.connect_signals(client)
            log("DNF5_ROOT : building transaction")
            content, rc = self._build_translations(pkgs, client)
            log(f"DNF5_ROOT : build transaction: rc =  {rc}")
            errors = client.session.get_transaction_problems_string()
            for error in errors:
                log(f"DNF5_ROOT : build transaction: error =  {error}")
            self.progress.hide()
            if rc == 0 or rc == 1:
                return TransactionResult(True, data=self.build_result(content))
            elif rc == 2:
                error_msgs = "\n".join(errors)
                return TransactionResult(False, error=error_msgs)

    def run_transaction(self) -> TransactionResult:
        self.download_queue.clear()
        with Dnf5DbusClient() as client:
            self.progress.show()
            self.progress.set_title(_("Building Transaction"))
            self.connect_signals(client)
            log("DNF5_ROOT : building transaction")
            self._build_translations(self.last_transaction, client)
            self.progress.set_title(_("Applying Transaction"))
            log("DNF5_ROOT : running transaction")
            client.do_transaction({})
            self.progress.hide()
            return TransactionResult(True, data=None)

    def on_download_add_new(self, session, package_id, name, size):
        pkg = DownloadPackage(package_id, name, size)
        self.download_queue.add(pkg)
        log(
            f"DNF5_ROOT : Signal : download_add_new: name: {name} size: {size} id: {package_id}"
        )
        if len(self.download_queue) == 1:
            match pkg.package_type:
                case DownloadType.PACKAGE:
                    self.progress.set_title(_("Download Packages"))
                case DownloadType.REPO:
                    self.progress.set_title(_("Download Reposiory Information"))
                case DownloadType.UNKNOWN:
                    log(f"DNF5_ROOT : unknown download type : {pkg.id}")
        self.progress.set_subtitle(_(f"Downloading : {name}"))

    def on_download_progress(self, session, package_id, to_download, downloaded):
        pkg: DownloadPackage = self.download_queue.get(package_id)
        log(
            f"DNF5_ROOT : Signal : download_progress: {pkg.name} ({downloaded}/{to_download})"
        )
        self.progress.set_subtitle(_(f"Downloading : {pkg.name}"))
        match pkg.package_type:
            case DownloadType.PACKAGE:
                pkg.downloaded = downloaded
            case DownloadType.REPO:
                if to_download > 0:
                    pkg.downloaded = downloaded
                    pkg.to_download = to_download
            case DownloadType.UNKNOWN:
                log(f"DNF5_ROOT : unknown download type : {pkg.id}")
        fraction = self.download_queue.fraction
        self.progress.set_progress(fraction)

    def on_download_end(self, session, package_id, rc, msg):
        pkg: DownloadPackage = self.download_queue.get(package_id)
        log(f"DNF5_ROOT : Signal : download_end: {pkg.name} rc: {rc} msg: {msg}")
        if rc == 0:
            match pkg.package_type:
                case DownloadType.PACKAGE:
                    pkg.downloaded = pkg.to_download
                    if self.download_queue.is_completted:
                        self.progress.set_title(_("Applying Transaction"))
                case DownloadType.REPO:
                    pkg.downloaded = 1
                    pkg.to_download = 1
                case DownloadType.UNKNOWN:
                    log(f"DNF5_ROOT : unknown download type : {pkg.id}")
        fraction = self.download_queue.fraction
        self.progress.set_progress(fraction)

    def on_repo_key_import_request(self, *args):
        log(f"DNF5_ROOT : Signal : repo_key_import_request: {args}")
