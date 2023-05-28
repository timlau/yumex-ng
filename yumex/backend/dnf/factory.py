from yumex.backend.interface import PackageRootBackend, Presenter, PackageBackend
from yumex.utils.enums import PackageBackendType


class DnfBackendFactory:
    def __init__(self, backend_type: PackageBackendType, presenter: Presenter):
        self.type: PackageBackendType = backend_type
        self.presenter: Presenter = presenter

    def get_backend(self) -> PackageBackend:
        match self.type:
            case PackageBackendType.DNF4:
                return self.get_dnf4_backend()
            case PackageBackendType.DNF5:
                return self.get_dnf5_backend()

    def get_root_backend(self) -> PackageBackend:
        match self.type:
            case PackageBackendType.DNF4:
                return self.get_dnf4_root_backend()
            case PackageBackendType.DNF5:
                return self.get_dnf5_root_backend()

    def get_dnf4_backend(self) -> PackageBackend:
        from yumex.backend.dnf.dnf4 import DnfCallback, Backend as Dnf4Backend

        callback = DnfCallback(self.presenter.get_main_window())

        return Dnf4Backend(callback=callback)

    def get_dnf5_backend(self) -> PackageBackend:
        from yumex.backend.dnf.dnf5 import Backend as Dnf5Backend

        return Dnf5Backend(self.presenter)

    def get_dnf4_root_backend(self) -> PackageRootBackend:
        from yumex.backend.daemon import YumexRootBackend

        return YumexRootBackend(self.presenter)

    def get_dnf5_root_backend(self) -> PackageRootBackend:
        from yumex.backend.dnf5daemon import YumexRootBackend

        return YumexRootBackend(self.presenter)
