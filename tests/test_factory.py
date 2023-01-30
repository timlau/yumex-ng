from unittest.mock import Mock
from yumex.backend.dnf.factory import DnfBackendFactory
from yumex.utils.enums import PackageBackendType
from yumex.backend.dnf.dnf4 import Backend as Dnf4Backend
from yumex.backend.dnf.dnf5 import Backend as Dnf5Backend


def test_DNF4(mocker):
    # do not do a real dnf setup, so we mock the DnfBase class
    mocker.patch("yumex.backend.dnf.dnf4.DnfBase")
    presenter = Mock()
    factory = DnfBackendFactory(PackageBackendType.DNF4, presenter=presenter)
    backend = factory.get_backend()
    assert isinstance(backend, Dnf4Backend)


def test_DNF5(mocker):
    mocker.patch("yumex.backend.dnf.dnf5.dnf")
    presenter = Mock()
    factory = DnfBackendFactory(PackageBackendType.DNF5, presenter=presenter)
    backend = factory.get_backend()
    assert isinstance(backend, Dnf5Backend)
