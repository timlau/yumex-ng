from yumex.backend.interface import PackageBackend, PackageRootBackend, Presenter
from yumex.utils.enums import PackageBackendType


class DnfBackendFactory:
    def __init__(self, backend_type: PackageBackendType, presenter: Presenter):
        self.type: PackageBackendType = backend_type
        self.presenter: Presenter = presenter

    def get_backend(self) -> PackageBackend:
        return self.get_dnf5_backend()

    def get_root_backend(self) -> PackageBackend:
        return self.get_dnf5_root_backend()

    def get_dnf5_backend(self) -> PackageBackend:
        from yumex.backend.dnf.dnf5 import Backend as Dnf5Backend

        return Dnf5Backend(self.presenter)

    def get_dnf5_root_backend(self) -> PackageRootBackend:
        from yumex.backend.dnf5daemon import YumexRootBackend

        return YumexRootBackend(self.presenter)
