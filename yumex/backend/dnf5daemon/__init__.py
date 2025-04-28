import datetime
import logging
from dataclasses import asdict, dataclass, field
from typing import Iterable, Self

import dbus

from yumex.backend import TransactionResult
from yumex.backend.dnf import TransactionOptions, YumexPackage
from yumex.backend.dnf5daemon.filter import FilterUpdates
from yumex.backend.interface import Presenter, Progress
from yumex.utils.enums import (
    DownloadType,
    InfoType,
    PackageFilter,
    PackageState,
    PackageTodo,
    ScriptType,
    TransactionAction,
    TransactionCommand,
)

from .client import Dnf5DbusClient

logger = logging.getLogger(__name__)

ADVISOR_ATTRS = [
    "advisoryid",
    "name",
    "title",
    "type",
    "severity",
    "status",
    "description",
    "buildtime",
    "references",
]

PACKAGE_ATTRS = [
    "name",
    "evr",
    "arch",
    "repo_id",
    "summary",
    "install_size",
    "is_installed",
]


def create_package(pkg) -> YumexPackage:
    """Generate a YumexPackage from a dnf5daemon list package"""
    evr = pkg["evr"]
    if ":" in evr:
        e, vr = evr.split(":")
    else:
        vr = evr
        e = 0
    v, r = vr.split("-")
    state = PackageState.INSTALLED if pkg["is_installed"] else PackageState.AVAILABLE
    return YumexPackage(
        name=str(pkg["name"]),
        arch=str(pkg["arch"]),
        epoch=e,
        release=r,
        version=v,
        repo=str(pkg["repo_id"]),
        description=str(pkg["summary"]),
        size=pkg["install_size"],
        state=state,
    )


def get_action(action: TransactionAction) -> str:
    match action:
        case TransactionAction.INSTALL:
            return _("Installing")
        case TransactionAction.UPGRADE:
            return _("Upgrading")
        case TransactionAction.DOWNGRADE:
            return _("Downgrading")
        case TransactionAction.REINSTALL:
            return _("Reinstalling")
        case TransactionAction.REMOVE:
            return _("Removing")
        case TransactionAction.REPLACED:
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
class UpdateInfo:
    id: str
    title: str
    description: str
    type: str
    updated: str
    references: list

    def as_dict(self):
        """return dataclass as a dict"""
        return asdict(self)


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
        self.client = Dnf5DbusClient()
        self.client.open_session()
        self.connect_signals()
        repo_prioritiy = {id: priority for id, _, _, priority in self.get_repositories()}
        self.filter_updates = FilterUpdates(repo_prioritiy, self.get_packages_by_name)
        self._installed_evr = self.fetch_installed_evr()
        self._offline = False

    def fetch_installed_evr(self) -> list[YumexPackage]:
        """build dict of installed package name and evr"""
        inst_dict = {}
        for pkg in self.installed:
            if pkg["name"] not in inst_dict:
                inst_dict[pkg["name"]] = pkg["evr"]
        return inst_dict

    def reset(self):
        # self.client.close_session()
        # self.client.open_session()
        # self.connect_signals()
        logger.debug(f"DBUS: {self.client.session_base.dbus_interface}.reset()")
        self.client.session_base.reset()
        logger.debug("Dnf5Demon is reset...")
        self._installed_evr = self.fetch_installed_evr()

    def close(self):
        self.client.close_session()

    @property
    def progress(self) -> Progress:
        return self.presenter.progress

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        pass

    def build_result(self, content: list) -> dict:
        result_dict = {}
        for i, (typ, action, _, _, pkg) in enumerate(content):
            action = action.lower()
            if action.strip() == "":
                action = typ.lower()
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

    def _build_transations(self, pkgs: list, opts: TransactionOptions) -> tuple[list, int]:
        to_install = []
        to_update = []
        to_remove = []
        to_downgrade = []
        to_reinstall = []
        to_distrosync = []
        allow_erasing = False
        self.client.session_goal.reset()
        if opts.command == TransactionCommand.SYSTEM_UPGRADE:
            res, err = self.system_upgrade("systemupgrade", opts.parameter)
            allow_erasing = True
        elif opts.command == TransactionCommand.SYSTEM_DISTRO_SYNC:
            to_distrosync = [pkg.na for pkg in self._get_yumex_packages(self.installed)]
            logger.debug(f"DBUS: {self.client.session_rpm.dbus_interface}.distrosync()")
            self.client.session_rpm.distro_sync(dbus.Array(to_distrosync), dbus.Dictionary({}))
        elif opts.command == TransactionCommand.IS_FILE:
            logger.debug(f"adding files for install : {pkgs}")
            to_install = pkgs
            logger.debug(f"DBUS: {self.client.session_rpm.dbus_interface}.install()")
            self.client.session_rpm.install(dbus.Array(to_install), dbus.Dictionary({}))
        else:
            for pkg in pkgs:
                match pkg.todo:
                    case PackageTodo.INSTALL:
                        logger.debug(f"adding {pkg.nevra} for install")
                        to_install.append(pkg.nevra)
                    case PackageTodo.UPDATE:
                        logger.debug(f"adding {pkg.nevra} for update")
                        to_update.append(pkg.nevra)
                    case PackageTodo.REMOVE:
                        logger.debug(f"adding {pkg.nevra} for remove")
                        to_remove.append(pkg.nevra)
                    case PackageTodo.DOWNGRADE:
                        logger.debug(f"adding {pkg.na} for downgrade")
                        to_downgrade.append(pkg.na)
                    case PackageTodo.REINSTALL:
                        logger.debug(f"adding {pkg.nevra} for reinstall")
                        to_reinstall.append(pkg.nevra)
                    case PackageTodo.DISTROSYNC:
                        logger.debug(f"adding {pkg.na} for distrosync")
                        to_distrosync.append(pkg.na)
                    case _:
                        logger.debug(f"error in {pkg.nevra} todo: {pkg.todo}")
            if to_remove:
                logger.debug(f"DBUS: {self.client.session_rpm.dbus_interface}.remove()")
                self.client.session_rpm.remove(dbus.Array(to_remove), dbus.Dictionary({}))
            if to_install:
                logger.debug(f"DBUS: {self.client.session_rpm.dbus_interface}.install()")
                self.client.session_rpm.install(dbus.Array(to_install), dbus.Dictionary({}))

            if to_update:
                logger.debug(f"DBUS: {self.client.session_rpm.dbus_interface}.update()")
                self.client.session_rpm.upgrade(dbus.Array(to_update), dbus.Dictionary({}))

            if to_downgrade:
                logger.debug(f"DBUS: {self.client.session_rpm.dbus_interface}.downgrade()")
                self.client.session_rpm.downgrade(dbus.Array(to_downgrade), dbus.Dictionary({}))
                allow_erasing = True
            if to_reinstall:
                logger.debug(f"DBUS: {self.client.session_rpm.dbus_interface}.reinstall()")
                self.client.session_rpm.reinstall(dbus.Array(to_reinstall), dbus.Dictionary({}))
            if to_distrosync:
                logger.debug(f"DBUS: {self.client.session_rpm.dbus_interface}.distrosync()")
                self.client.session_rpm.distro_sync(dbus.Array(to_distrosync), dbus.Dictionary({}))

        res, err = self.client.resolve(dbus.Dictionary({"allow_erasing": allow_erasing}))
        if res:
            result, rc = res
        else:
            result, rc = ([], 2)
        return result, rc

    def connect_signals(self):
        self.client.session_base.connect_to_signal("download_add_new", self.on_download_add_new)
        self.client.session_base.connect_to_signal("download_progress", self.on_download_progress)
        self.client.session_base.connect_to_signal("download_end", self.on_download_end)
        self.client.session_base.connect_to_signal("download_mirror_failure", self.on_download_mirror_failure)
        self.client.session_base.connect_to_signal("repo_key_import_request", self.on_repo_key_import_request)
        self.client.session_rpm.connect_to_signal("transaction_action_start", self.on_transaction_action_start)
        self.client.session_rpm.connect_to_signal("transaction_action_progress", self.on_transaction_action_progress)
        self.client.session_rpm.connect_to_signal("transaction_action_stop", self.on_transaction_action_stop)
        self.client.session_rpm.connect_to_signal("transaction_before_begin", self.on_transaction_before_begin)
        self.client.session_rpm.connect_to_signal("transaction_after_complete", self.on_transaction_after_complete)
        self.client.session_rpm.connect_to_signal("transaction_script_start", self.on_transaction_script_start)
        self.client.session_rpm.connect_to_signal("transaction_script_stop", self.on_transaction_script_stop)
        self.client.session_rpm.connect_to_signal("transaction_verify_start", self.on_transaction_verify_start)
        self.client.session_rpm.connect_to_signal("transaction_verify_progress", self.on_transaction_verify_progress)
        self.client.session_rpm.connect_to_signal("transaction_verify_stop", self.on_transaction_verify_stop)

    def build_transaction(self, pkgs: list, opts: TransactionOptions) -> TransactionResult:
        self.last_transaction = pkgs
        self.progress.show()
        self.progress.set_title(_("Building Transaction"))
        logger.debug("building transaction")
        content, rc = self._build_transations(pkgs, opts)
        logger.debug(f"build transaction: rc =  {rc}")
        errors = self.client.session_goal.get_transaction_problems_string()
        for error in errors:
            logger.debug(f"build transaction: error =  {error}")
        self.progress.hide()
        if rc == 0:
            return TransactionResult(True, data=self.build_result(content))
        if rc == 1:
            return TransactionResult(True, data=self.build_result(content), problems=list(errors))
        else:
            error_msgs = "\n".join(errors)
            return TransactionResult(False, error=error_msgs)

    def run_transaction(self, opts: TransactionOptions) -> TransactionResult:
        self._offline = opts.offline
        self.download_queue.clear()
        self.progress.show()
        self.progress.set_title(_("Building Transaction"))
        logger.debug("building transaction")
        self._build_transations(self.last_transaction, opts)  # type: ignore
        # self.progress.set_title(_("Applying Transaction"))
        logger.debug("running transaction")
        if opts.offline:
            res, err = self.client.do_transaction({"offline": True})
        else:
            res, err = self.client.do_transaction()
        logger.debug(f"transaction rc: {res} error: {err}")
        # self.progress.hide()
        if err:
            return TransactionResult(False, error=err)
        else:
            return TransactionResult(True, data=None)  # type: ignore

    def on_download_mirror_failure(self, session, *args):
        logger.debug(f"SIGNAL : download_mirror_failure ({args})")

    def on_transaction_before_begin(self, session, *args):
        logger.debug(f"SIGNAL : transaction_before_begin ({args})")
        if self._offline:
            self.progress.set_title(_("Building Offline Transaction"))
        else:
            self.progress.set_title(_("Applying Transaction"))

    def on_transaction_after_complete(self, session, *args):
        logger.debug(f"SIGNAL : transaction_after_complete ({args})")
        self.progress.hide()

    def on_transaction_verify_start(self, session, total):
        logger.debug(f"SIGNAL : transaction_verify_start ({total})")
        self.progress.set_title(_("Verifying Packages"))
        self.progress.set_progress(0.0)

    def on_transaction_verify_progress(self, session, amount, total):
        logger.debug(f"SIGNAL : transaction_verify_progress ({amount}/{total})")
        if total > 0:
            self.progress.set_progress(amount / total)

    def on_transaction_verify_stop(self, session, total):
        logger.debug(f"SIGNAL : transaction_verify_stop ({total})")
        self.progress.set_progress(1.0)
        self.progress.set_title(_("Applying Transaction"))

    def on_transaction_script_start(self, session, pkg, typ, *args):
        script_type = str(ScriptType(typ))
        logger.debug(f"SIGNAL : transaction_script_start : {pkg} ({script_type}) ({args})")
        self.progress.set_subtitle(_("Running Scripts") + f" ({script_type}) : {pkg}")
        self.progress.set_progress(0.0)

    def on_transaction_script_stop(self, session, pkg, *args):
        logger.debug(f"SIGNAL : transaction_script_stop : {pkg} {args}")
        self.progress.set_progress(1.0)

    def on_transaction_action_start(self, session, package_id, action, total):
        logger.debug(f"SIGNAL : transaction_action_start: action {action} total: {total} id: {package_id}")
        action_str = get_action(action)
        self.progress.set_subtitle(f" {action_str} {package_id}")
        self.progress.set_progress(0.0)

    def on_transaction_action_progress(self, session, package_id, amount, total):
        logger.debug(f"SIGNAL : transaction_action_progress: amount {amount} total: {total} id: {package_id}")
        if total > 0:
            self.progress.set_progress(amount / total)

    def on_transaction_action_stop(self, session, package_id, total):
        logger.debug(f"SIGNAL : transaction_action_stop: total: {total} id: {package_id}")
        self.progress.set_progress(0.0)

    def on_download_add_new(self, session, *args):
        if len(args) == 3:
            download_id, pkg_name, total_to_download = args
        else:
            logger.debug(f"SIGNAL: download_add_new unexpected args: {args}")
            return
        logger.debug(
            f"SIGNAL : download_add_new: download_id: {download_id}"
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
            logger.debug(f"SIGNAL: download_progress: unexpected args: {args}")
            return
        logger.debug(
            f"SIGNAL : download_progress: download_id: {download_id}"
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
            logger.debug(f"SIGNAL: download_end: unexpected args: {args}")
            return
        logger.debug(f"SIGNAL : download_end: download_id: {download_id} status: {status} msg: {msg}")
        pkg: DownloadPackage = self.download_queue.get(download_id)  # type: ignore
        if status == 0:
            match pkg.package_type:
                case DownloadType.PACKAGE:
                    pkg.downloaded = pkg.to_download
                    if self.download_queue.is_completed:
                        if self._offline:
                            self.progress.set_title(_("Building Offline Transaction"))
                        else:
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
            f"SIGNAL : repo_key_import_request: {session, key_id, user_ids, key_fingerprint, key_url, timestamp}"
        )
        # <arg name="session_object_path" type="o" />
        # <arg name="key_id" type="s" />
        # <arg name="user_ids" type="as" />
        # <arg name="key_fingerprint" type="s" />
        # <arg name="key_url" type="s" />
        # <arg name="timestamp" type="x" />
        logger.debug(f"confirm gpg key import id: {key_id} user-id: {user_ids[0]}")
        key_values = (key_id, user_ids[0], key_fingerprint, key_url, timestamp)
        self.presenter.progress.hide(clear=False)
        ok = self.presenter.confirm_gpg_import(key_values)
        self.presenter.progress.show()
        if ok:
            logger.debug("Importing RPM GPG key")
            self.client.confirm_key(key_id, True)
        else:
            logger.debug("Denied RPM GPG key")
            self.client.confirm_key(key_id, False)

    def check_for_downgrades(self, pkgs: list[YumexPackage]) -> list[YumexPackage]:
        """check for downgrades"""
        for pkg in pkgs:
            if pkg.name in self._installed_evr:
                if pkg.evr < self._installed_evr[pkg.name]:
                    pkg.set_state(PackageState.DOWNGRADE)
        return pkgs

    # Implement PackageBackend

    @property
    def package_attr(self) -> list[str]:
        return PACKAGE_ATTRS

    def get_packages(self, pkg_filter: PackageFilter) -> list[YumexPackage]:
        match pkg_filter:
            case PackageFilter.AVAILABLE:
                return self._get_yumex_packages(self.available)
            case PackageFilter.INSTALLED:
                return self._get_yumex_packages(self.installed)
            case PackageFilter.UPDATES:
                updates = self._get_yumex_packages(self.updates, state=PackageState.UPDATE)
                return self.filter_updates.get_updates(updates)
            case other:
                raise ValueError(f"Unknown package filter: {other}")

    def search(self, txt: str, options={}) -> list[YumexPackage]:
        kw_args = options
        kw_args["package_attrs"] = self.package_attr
        if "*" not in txt:
            txt = f"*{txt}*"
        result = self.client.package_list_fd(txt, **kw_args)
        if result:
            pkgs = self.check_for_downgrades(self._get_yumex_packages(result))
            return pkgs
        else:
            return []

    def _get_package_attribute(self, pkg: YumexPackage, attribute: str):
        result = self.client.package_list_fd(
            pkg.nevra,
            package_attrs=["nevra", attribute],
            scope="all",
        )
        if result:
            return result[0][attribute]
        return None

    def _get_description(self, pkg: YumexPackage):
        desc = self._get_package_attribute(pkg, "description")
        if desc:
            return desc
        return ""

    def _get_files(self, pkg: YumexPackage):
        files = self._get_package_attribute(pkg, "files")
        if files:
            return files
        return []

    def _get_update_info(self, pkg: YumexPackage):
        info_list = []
        result, error = self.client.advisory_list(pkg.name, advisor_attrs=ADVISOR_ATTRS)
        if result:
            for res in result:
                # print(res)
                timestamp = datetime.datetime.fromtimestamp(res["buildtime"])
                updated = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                info_list.append(
                    UpdateInfo(
                        id=res["name"],
                        title=res["title"],
                        description=res["description"],
                        type=res["severity"],
                        updated=updated,
                        references=res["references"],
                    ).as_dict()
                )
            return info_list
        return []

    def get_package_info(self, pkg: YumexPackage, attr: InfoType):
        match attr:
            case InfoType.DESCRIPTION:
                return self._get_description(pkg)
            case InfoType.FILES:
                return self._get_files(pkg)
            case InfoType.UPDATE_INFO:
                return self._get_update_info(pkg)
            case other:
                raise ValueError(f"Unknown package info: {other}")

    def get_repositories(self) -> list[str]:
        repos, error = self.client.repo_list()
        if error:
            self.presenter.show_message(error)
        else:
            return [(repo["id"], repo["name"], repo["enabled"], repo["priority"]) for repo in repos]

    def depsolve(self, pkgs: Iterable[YumexPackage]) -> list[YumexPackage]:
        dep_pkgs = []
        opts = TransactionOptions()
        res, rc = self._build_transations(pkgs, opts)
        for elem in res:
            _, action, typ, _, pkg_dict = elem
            pkg_dict["summary"] = ""  # need for create package, not need for depsolve
            if action == "Install":
                pkg_dict["is_installed"] = False
            else:
                pkg_dict["is_installed"] = True
            ypkg = create_package(pkg_dict)
            if typ != "User":
                ypkg.is_dep = True
                dep_pkgs.append(ypkg)
                logger.debug(f"Adding {ypkg} as dependency")
        return self.check_for_downgrades(dep_pkgs)

    # Helpers (PackageBackend)

    @property
    def installed(self) -> list[dict[str, any]]:
        result = self.client.package_list_fd(
            "*",
            package_attrs=self.package_attr,
            scope="installed",
        )
        return result

    @property
    def available(self) -> list[dict[str, any]]:
        result = self.client.package_list_fd(
            "*",
            package_attrs=self.package_attr,
            scope="available",
        )
        return result

    @property
    def updates(self) -> list[dict[str, any]]:
        updates = self.client.package_list_fd(
            "*",
            package_attrs=self.package_attr,
            scope="upgrades",
        )
        if updates:
            return updates
        else:
            return []

    def _get_yumex_packages(self, pkgs: list[dict[str, any]], state=PackageState.AVAILABLE) -> list[YumexPackage]:
        nevra_dict = {}
        for pkg in pkgs:
            ypkg: YumexPackage = create_package(pkg)
            if state == PackageState.UPDATE:
                ypkg.set_state(PackageState.UPDATE)
            if ypkg.nevra not in nevra_dict:
                nevra_dict[ypkg.nevra] = ypkg
            # else:
            #     logger.debug(f"Skipping duplicate : {ypkg}")
        return list(nevra_dict.values())

    def get_packages_by_name(self, pkg: YumexPackage) -> list[YumexPackage]:
        """Get a list of packages by name"""
        result = self.client.package_list_fd(
            pkg.name,
            package_attrs=self.package_attr,
            scope="available",
            arch=[pkg.arch],
            latest_limit=10,
        )
        return self._get_yumex_packages(result)

    def has_offline_transaction(self) -> bool:
        """Check if there is an offline transaction"""
        pending, _ = self.client.offline_get_status()
        return pending

    def cancel_offline_transaction(self) -> bool:
        """Cancel the offline transaction"""
        if not self.has_offline_transaction():
            return False, ["No offline transaction found"]
        success, err_mesg = self.client.offline_clean()
        return success, err_mesg

    def reboot_and_install(self) -> bool:
        """Reboot and install the system upgrade"""
        if not self.has_offline_transaction():
            return False, ["No offline transaction found"]
        success, err_mesg = self.client.offline_reboot()
        return success, err_mesg

    def system_upgrade(self, mode, releasever):
        self.reopen_session({"releasever": releasever})
        options = dbus.Dictionary({"mode": "upgrade", "releasever": releasever})
        res, err = self.client.system_upgrade(options)
        return res, err

    def reopen_session(self, options={}):
        self.client.reopen_session(options)
        self.connect_signals()
