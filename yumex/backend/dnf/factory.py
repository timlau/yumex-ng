from yumex.backend.interface import Presenter
from yumex.utils.enums import PackageBackendType


class DnfBackendFactory:
    def __init__(self, backend_type: PackageBackendType, presenter: Presenter):
        self.type: PackageBackendType = backend_type
        self.presenter = presenter

    def get_backend(self):
        match self.type:
            case PackageBackendType.DNF4:
                return self.get_dnf4_backend()
            case PackageBackendType.DNF5:
                return self.get_dnf5_backend()

    def get_dnf4_backend(self):
        from yumex.backend.dnf.dnf4 import DnfCallback, Backend as Dnf4Backend

        callback = DnfCallback(self.presenter.win)

        return Dnf4Backend(callback=callback)

    def get_dnf5_backend(self):
        from yumex.backend.dnf.dnf5 import Backend as Dnf5Backend

        return Dnf5Backend(self.presenter)
