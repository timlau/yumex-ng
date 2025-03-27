import logging
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import Iterable, Self

from yumex.backend import TransactionResult
from yumex.backend.dnf import YumexPackage
from yumex.backend.interface import Presenter, Progress
from yumex.utils.enums import InfoType, PackageFilter, PackageState, SearchField

from .client import Dnf5DbusClient, gv_list

logger = logging.getLogger(__name__)


def create_package(pkg) -> YumexPackage:
    """Generate a YumexPackage from a dnf5daemon list package"""
    evr = pkg["evr"]
    if ":" in evr:
        vr = evr.split(":")[1]
    else:
        vr = evr
    v, r = vr.split("-")
    state = PackageState.INSTALLED if pkg["is_install"] else PackageState.AVAILABLE
    return YumexPackage(
        name=pkg["name"],
        arch=pkg["arch"],
        epoch=pkg["epoch"],
        release=r,
        version=v,
        repo=pkg["repo_id"],
        description=pkg["summary"],
        size=pkg["install_size"],
        state=state,
    )


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
        self.presenter: Presenter = presenter
        self.last_transaction = None
        self.download_queue = DownloadQueue()
        self.client = None

    @property
    def progress(self) -> Progress:
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
                logger.debug("no size found : {pkg}")
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
                    logger.debug(f"adding {pkg.nevra} for install")
                    to_install.append(pkg.nevra)
                case PackageState.UPDATE:
                    logger.debug(f"adding {pkg.nevra} for update")
                    to_update.append(pkg.nevra)
                case PackageState.INSTALLED:
                    logger.debug(f"adding {pkg.nevra} for remove")
                    to_remove.append(pkg.nevra)
        if to_remove:
            client.session.remove(gv_list(to_remove), {})
        if to_install:
            client.session.install(gv_list(to_install), {})
        if to_update:
            client.session.upgrade(gv_list(to_update), {})
        res = client.resolve({})
        if res:
            content, rc = res
        else:  # Something went very wrong
            content, rc = [], 2
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
            logger.debug("dnf5 5.1.13 or higher required for transaction signals")

    def build_transaction(self, pkgs: list[YumexPackage]) -> TransactionResult:
        self.last_transaction = pkgs
        with Dnf5DbusClient() as client:
            self.client = client
            self.progress.show()
            self.progress.set_title(_("Building Transaction"))
            self.connect_signals(client)
            logger.debug("building transaction")
            content, rc = self._build_transations(pkgs, client)
            logger.debug(f"build transaction: rc =  {rc}")
            errors = client.session.get_transaction_problems_string()
            for error in errors:
                logger.debug(f"build transaction: error =  {error}")
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
            logger.debug("building transaction")
            self._build_transations(self.last_transaction, client)  # type: ignore
            self.progress.set_title(_("Applying Transaction"))
            logger.debug("running transaction")
            res = client.do_transaction()
            logger.debug(f"transaction rc: {res}")
            self.progress.hide()
            if res:
                return TransactionResult(False, error=res)
            else:
                return TransactionResult(True, data=None)  # type: ignore

    def on_transaction_action_start(self, session, package_id, action, total):
        logger.debug(f"Signal : transaction_action_start: action {action} total: {total} id: {package_id}")
        action_str = get_action(action)
        self.progress.set_subtitle(f" {action_str} {package_id}")

    def on_transaction_action_progress(self, session, package_id, amount, total):
        logger.debug(f"Signal : transaction_action_progress: amount {amount} total: {total} id: {package_id}")

    def on_transaction_action_stop(self, session, package_id, total):
        logger.debug(f"Signal : transaction_action_stop: total: {total} id: {package_id}")

    def on_download_add_new(self, session, *args):
        if len(args) == 3:
            download_id, pkg_name, total_to_download = args
        else:
            logger.debug(f"Signal: download_add_new unexpected args: {args}")
            return
        logger.debug(
            f"Signal : download_add_new: download_id: {download_id}"
            f" total_to_download: {total_to_download}"
            f" pkg_name: {pkg_name}"
        )
        pkg = DownloadPackage(download_id, pkg_name, total_to_download)
        self.download_queue.add(pkg)
        if len(self.download_queue) == 1:
            match pkg.package_type:
                case DownloadType.PACKAGE:
                    self.progress.set_title(_("Download Packages"))
                case DownloadType.REPO:
                    self.progress.set_title(_("Download Reposiory Information"))
                case DownloadType.UNKNOWN:
                    logger.debug(f"unknown download type : {pkg.id}")
        self.progress.set_subtitle(_(f"Downloading : {pkg_name}"))

    def on_download_progress(self, session, *args):
        if len(args) == 3:
            download_id, total_to_download, downloaded = args
        else:
            logger.debug(f"Signal: download_progress: unexpected args: {args}")
            return
        logger.debug(
            f"Signal : download_progress: download_id: {download_id}"
            f" downloaded: {downloaded} total_to_download: {total_to_download}"
        )
        pkg: DownloadPackage = self.download_queue.get(download_id)  # type: ignore
        self.progress.set_subtitle(_(f"Downloading : {pkg.name}"))
        match pkg.package_type:
            case DownloadType.PACKAGE:
                pkg.downloaded = downloaded
            case DownloadType.REPO:
                if total_to_download > 0:
                    pkg.downloaded = downloaded
                    pkg.to_download = total_to_download
            case DownloadType.UNKNOWN:
                logger.debug(f"unknown download type : {pkg.id}")
        fraction = self.download_queue.fraction
        self.progress.set_progress(fraction)

    def on_download_end(self, session, *args):
        if len(args) == 3:
            download_id, status, msg = args
        else:
            logger.debug(f"Signal: download_end: unexpected args: {args}")
            return
        logger.debug(f"Signal : download_end: download_id: {download_id} status: {status} msg: {msg}")
        pkg: DownloadPackage = self.download_queue.get(download_id)  # type: ignore
        if status == 0:
            match pkg.package_type:
                case DownloadType.PACKAGE:
                    pkg.downloaded = pkg.to_download
                    if self.download_queue.is_completed:
                        self.progress.set_title(_("Applying Transaction"))
                case DownloadType.REPO:
                    pkg.downloaded = 1
                    pkg.to_download = 1
                case DownloadType.UNKNOWN:
                    logger.debug(f"unknown download type : {pkg.id}")
        fraction = self.download_queue.fraction
        self.progress.set_progress(fraction)

    def on_repo_key_import_request(self, session, key_id, user_ids, key_fingerprint, key_url, timestamp):
        logger.debug(
            f"Signal : repo_key_import_request: {session, key_id, user_ids, key_fingerprint, key_url, timestamp}"
        )
        # <arg name="session_object_path" type="o" />
        # <arg name="key_id" type="s" />
        # <arg name="user_ids" type="as" />
        # <arg name="key_fingerprint" type="s" />
        # <arg name="key_url" type="s" />
        # <arg name="timestamp" type="x" />
        logger.debug(f"confirm gpg key import id: {key_id} user-id: {user_ids[0]}")
        key_values = (key_id, user_ids[0], key_fingerprint, key_url, timestamp)
        ok = self.presenter.confirm_gpg_import(key_values)
        if ok:
            logger.debug("Importing RPM GPG key")
            self.client.confirm_key(key_id, True)
        else:
            logger.debug("Denied RPM GPG key")
            self.client.confirm_key(key_id, False)

    # Implement PackageBackend

    def get_packages(self, pkg_filter: PackageFilter) -> list[YumexPackage]:
        match pkg_filter:
            case PackageFilter.AVAILABLE:
                return self._get_yumex_packages(self.available)
            case PackageFilter.INSTALLED:
                return self._get_yumex_packages(self.installed)
            case PackageFilter.UPDATES:
                packages = self._get_yumex_packages(self.updates, state=PackageState.UPDATE)
                # return self.get_packages_with_lowest_priority(packages)
                return packages
            case other:
                raise ValueError(f"Unknown package filter: {other}")

    def search(self, txt: str, field: SearchField, limit: int) -> list[YumexPackage]: ...

    def get_package_info(self, pkg: YumexPackage, attr: InfoType) -> str | None: ...

    def get_repositories(self) -> list[str]: ...

    def depsolve(self, pkgs: Iterable[YumexPackage]) -> list[YumexPackage]: ...

    # Helpers (PackageBackend)

    @property
    def package_attr(self):
        return [
            "name",
            "evr",
            "arch",
            "repo_id",
            "summary",
            "install_size",
            "is_installed",
        ]

    @property
    def installed(self) -> list[dict[str, any]]:
        with Dnf5DbusClient() as client:
            return client.package_list(
                "*",
                package_attrs=self.package_attr,
                scope="installed",
            )

    @property
    def available(self) -> list[dict[str, any]]:
        with Dnf5DbusClient() as client:
            return client.package_list(
                "*",
                package_attrs=self.package_attr,
                scope="available",
            )

    @property
    def updates(self) -> list[dict[str, any]]:
        with Dnf5DbusClient() as client:
            return client.package_list(
                "*",
                package_attrs=self.package_attr,
                scope="upgrades",
            )

    def _get_yumex_packages(self, pkgs: list[dict[str, any]], state=PackageState.AVAILABLE) -> list[YumexPackage]:
        nevra_dict = {}
        for pkg in pkgs:
            ypkg: YumexPackage = create_package(pkg)
            if state == PackageState.UPDATE:
                ypkg.set_state(PackageState.UPDATE)
            if ypkg.nevra not in nevra_dict:
                nevra_dict[ypkg.nevra] = ypkg
            else:
                logger.debug(f"Skipping duplicate : {ypkg}")
        return list(nevra_dict.values())
