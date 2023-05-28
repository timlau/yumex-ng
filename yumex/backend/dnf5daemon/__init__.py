from typing import Self
from yumex.backend.daemon import TransactionResult
from yumex.backend.dnf import YumexPackage

from yumex.ui.progress import YumexProgress
from yumex.utils import log
from yumex.utils.enums import PackageState

from .client import Dnf5DbusClient, gv_list


class YumexRootBackend:
    def __init__(self, presenter) -> None:
        super().__init__()
        self.presenter = presenter
        self.last_transaction = None

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
            size = pkg["package_size"].get_uint64()
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
            client.session.update(gv_list(to_update), {})
        res = client.session.resolve({})
        content, rc = res
        return content, rc

    def build_transaction(self, pkgs: list[YumexPackage]) -> TransactionResult:
        self.last_transaction = pkgs
        with Dnf5DbusClient() as client:
            self.progress.show()
            self.progress.set_title(_("Building Transaction"))
            log("DNF5_ROOT : building transaction")
            content, rc = self._build_translations(pkgs, client)
            log(f"DNF5_ROOT : build transaction: rc =  {rc}")
            errors = client.session.get_transaction_problems_string()
            log(f"DNF5_ROOT : build transaction: error =  {errors}")
            self.progress.hide()
            if rc == 0 or rc == 1:
                return TransactionResult(True, data=self.build_result(content))
            elif rc == 2:
                return TransactionResult(False, error=errors)

    def run_transaction(self) -> TransactionResult:
        with Dnf5DbusClient() as client:
            self.progress.show()
            self.progress.set_title(_("Building Transaction"))
            log("DNF5_ROOT : building transaction")
            self._build_translations(self.last_transaction, client)
            self.progress.set_title(_("Applying Transaction"))
            log("DNF5_ROOT : running transaction")
            client.session.do_transaction({})
            self.progress.hide()
            return TransactionResult(True, data=None)
