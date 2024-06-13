from dataclasses import dataclass, field
from enum import Enum, auto, IntEnum
from typing import Self

from yumex.backend import TransactionResult
from yumex.backend.dnf import YumexPackage

from yumex.backend.presenter import YumexPresenter
from yumex.ui.progress import YumexProgress
from yumex.utils import log
from yumex.utils.enums import PackageState

from .client import Dnf5DbusClient, gv_list, gv_string


# defined in include/libdnf5/transaction/transaction_item_action.hpp in dnf5 code
class Action(IntEnum):
    INSTALL = 1
    UPGRADE = 2
    DOWNGRADE = 3
    REINSTALL = 4
    REMOVE = 5
    REPLACED = 6
    REASON_CHANGE = 7
    ENABLE = 8
    DISABLE = 9
    RESET = 10


class DownloadType(Enum):
    REPO = auto()
    PACKAGE = auto()
    UNKNOWN = auto()


def get_action(action: Action) -> str:
    match action:
        case Action.INSTALL:
            return _("Installing")
        case Action.UPGRADE:
            return _("Upgrading")
        case Action.DOWNGRADE:
            return _("Downgrading")
        case Action.REINSTALL:
            return _("Reinstalling")
        case Action.REMOVE:
            return _("Removing")
        case Action.REPLACED:
            return _("Replacing")
    return ""


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
    queue: dict = field(default_factory=dict)

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
    def is_completed(self):
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
        self.presenter: YumexPresenter = presenter
        self.last_transaction = None
        self.download_queue = DownloadQueue()
        self.client = None

    @property
    def progress(self) -> YumexProgress:
        return self.presenter.progress

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        pass

    def build_result(self, content: list) -> dict:
        result_dict = {}
        for _, action, _, _, pkg in content:
            action = action.lower()
            if action not in result_dict:
                result_dict[action] = []
            name = pkg["name"]
            arch = pkg["arch"]
            evr = pkg["evr"]
            repo = pkg["repo_id"]
            if "package_size" in pkg:
                size = pkg["package_size"]
            elif "install_size" in pkg:
                size = pkg["install_size"]
            else:
                size = 0.0
                log("no size found : {pkg}")
            nevra = f"{name}-{evr}.{arch}"
            result_dict[action].append(((nevra, repo), size))
        return result_dict

    def _build_transations(self, pkgs: list[YumexPackage], client):
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
        # FIXME:need dnf5 5.1.13 for the signals to be available in introspection
        # we need to bump the requement to dnf5 3.1.13 and remove the try/except block.
        try:
            client.session.transaction_action_start.connect(self.on_transaction_action_start)
            client.session.transaction_action_progress.connect(self.on_transaction_action_progress)
            client.session.transaction_action_end.connect(self.on_transaction_action_stop)
        except AttributeError:
            log("DNF5_ROOT : dnf5 5.1.13 or higher required for transaction signals")

    def build_transaction(self, pkgs: list[YumexPackage]) -> TransactionResult:
        self.last_transaction = pkgs
        with Dnf5DbusClient() as client:
            self.client = client
            self.progress.show()
            self.progress.set_title(_("Building Transaction"))
            self.connect_signals(client)
            log("DNF5_ROOT : building transaction")
            content, rc = self._build_transations(pkgs, client)
            log(f"DNF5_ROOT : build transaction: rc =  {rc}")
            errors = client.session.get_transaction_problems_string()
            for error in errors:
                log(f"DNF5_ROOT : build transaction: error =  {error}")
            self.progress.hide()
            if rc == 0 or rc == 1:
                return TransactionResult(True, data=self.build_result(content))
            else:
                error_msgs = "\n".join(errors)
                return TransactionResult(False, error=error_msgs)

    def run_transaction(self) -> TransactionResult:
        self.download_queue.clear()
        with Dnf5DbusClient() as client:
            self.client = client
            self.progress.show()
            self.progress.set_title(_("Building Transaction"))
            self.connect_signals(client)
            log("DNF5_ROOT : building transaction")
            self._build_transations(self.last_transaction, client)  # type: ignore
            self.progress.set_title(_("Applying Transaction"))
            log("DNF5_ROOT : running transaction")
            client.do_transaction()
            self.progress.hide()
            return TransactionResult(True, data=None)  # type: ignore

    def on_transaction_action_start(self, session, package_id, action, total):
        log(f"DNF5_ROOT : Signal : transaction_action_start: action {action} total: {total} id: {package_id}")
        action_str = get_action(action)
        self.progress.set_subtitle(f" {action_str} {package_id}")

    def on_transaction_action_progress(self, session, package_id, amount, total):
        log(f"DNF5_ROOT : Signal : transaction_action_progress: amount {amount} total: {total} id: {package_id}")

    def on_transaction_action_stop(self, session, package_id, total):
        log(f"DNF5_ROOT : Signal : transaction_action_stop: total: {total} id: {package_id}")

    def on_download_add_new(self, session, package_id, name, size):
        pkg = DownloadPackage(package_id, name, size)
        self.download_queue.add(pkg)
        log(f"DNF5_ROOT : Signal : download_add_new: name: {name} size: {size} id: {package_id}")
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
        pkg: DownloadPackage = self.download_queue.get(package_id)  # type: ignore
        log(f"DNF5_ROOT : Signal : download_progress: {pkg.name} ({downloaded}/{to_download})")
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
        pkg: DownloadPackage = self.download_queue.get(package_id)  # type: ignore
        log(f"DNF5_ROOT : Signal : download_end: {pkg.name} rc: {rc} msg: {msg}")
        if rc == 0:
            match pkg.package_type:
                case DownloadType.PACKAGE:
                    pkg.downloaded = pkg.to_download
                    if self.download_queue.is_completed:
                        self.progress.set_title(_("Applying Transaction"))
                case DownloadType.REPO:
                    pkg.downloaded = 1
                    pkg.to_download = 1
                case DownloadType.UNKNOWN:
                    log(f"DNF5_ROOT : unknown download type : {pkg.id}")
        fraction = self.download_queue.fraction
        self.progress.set_progress(fraction)

    def on_repo_key_import_request(self, session, key_id, user_ids, key_fingerprint, key_url, timestamp):
        log(
            "DNF5_ROOT : Signal : repo_key_import_request: "
            f"{session, key_id, user_ids, key_fingerprint, key_url, timestamp}"
        )
        # <arg name="session_object_path" type="o" />
        # <arg name="key_id" type="s" />
        # <arg name="user_ids" type="as" />
        # <arg name="key_fingerprint" type="s" />
        # <arg name="key_url" type="s" />
        # <arg name="timestamp" type="x" />
        log(f"DNF5_ROOT : confirm gpg key import id: {key_id} user-id: {user_ids[0]}")
        self.presenter.show_message(_("Importing RPM GPG key"))
        self.client.confirm_key(key_id, True)
