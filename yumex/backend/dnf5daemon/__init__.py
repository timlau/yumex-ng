from typing import Self
from yumex.backend.daemon import TransactionResult
from yumex.backend.dnf import YumexPackage

from yumex.ui.progress import YumexProgress
from yumex.utils.enums import PackageState

from .client import Dnf5DbusClient, gv_list


class YumexRootBackend:
    def __init__(self, presenter) -> None:
        super().__init__()
        self.presenter = presenter

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
            size = pkg["package_size"].get_uint64()
            nevra = f"{name}-{evr}.{arch}"
            result_dict[action].append((nevra, size))
        return result_dict

    def build_transaction(self, pkgs: list[YumexPackage]) -> TransactionResult:
        with Dnf5DbusClient() as client:
            to_install = []
            to_update = []
            to_remove = []
            for pkg in pkgs:
                match pkg.state:
                    case PackageState.AVAILABLE:
                        to_install.append(pkg.nevra)
                    case PackageState.UPDATE:
                        to_update.append(pkg.nevra)
                    case PackageState.INSTALLED:
                        to_remove.append(pkg.nevra)
            if to_remove:
                client.session.remove(gv_list(to_remove), {})
            if to_install:
                client.session.remove(gv_list(to_install), {})
            if to_update:
                client.session.remove(gv_list(to_update), {})
            res = client.session.resolve({})
            content, rc = res
            return TransactionResult(rc == 0, data=self.build_result(content))
