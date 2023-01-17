import gi

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

import pytest
from gi.repository import Flatpak
from yumex.utils.enums import FlatpakLocation, FlatpakType
from .mock import Mock
from yumex.backend.flatpak import FlatpakPackage

pytestmark = pytest.mark.guitest


class MockFlatpakRef(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = "dk.yumex.Yumex"
        self.name = "Yum Extender"
        self.version = "4.99"
        self.summary = "This is a package manager"
        self.ref_string = "app/dk.yumex.Yumex/x86_64/stable"
        self.kind = Flatpak.RefKind.APP

    def get_name(self) -> str:
        return self.id

    def get_appdata_name(self) -> str:
        return self.name

    def get_appdata_version(self) -> str:
        return self.version

    def get_appdata_summary(self) -> str:
        return self.summary

    def format_ref(self):
        return self.ref_string

    def get_origin(self):
        return "flathub"

    def get_kind(self):
        return self.kind


@pytest.fixture
def flatpak_package():
    return FlatpakPackage(MockFlatpakRef(), location=FlatpakLocation.USER)


def test_fppackage_setup(flatpak_package):
    assert isinstance(flatpak_package, FlatpakPackage)


def test_fppackage_id(flatpak_package):
    assert flatpak_package.id == "dk.yumex.Yumex"


def test_fppackage_name(flatpak_package):
    assert flatpak_package.name == "Yum Extender"


def test_fppackage_version(flatpak_package):
    assert flatpak_package.version == "4.99"


def test_fppackage_summary(flatpak_package):
    assert flatpak_package.summary == "This is a package manager"


def test_fppackage_origin(flatpak_package):
    assert flatpak_package.origin == "flathub"


def test_fppackage_is_user(flatpak_package):
    assert flatpak_package.is_user is True
    flatpak_package.location = FlatpakLocation.SYSTEM
    assert flatpak_package.is_user is False


def test_fppackage_repr(flatpak_package):
    assert repr(flatpak_package) == "app/dk.yumex.Yumex/x86_64/stable"


def test_fppackage_type(flatpak_package):
    assert flatpak_package.type == FlatpakType.APP
    flatpak_package.ref.kind = Flatpak.RefKind.RUNTIME
    assert flatpak_package.type == FlatpakType.RUNTIME
    flatpak_package.ref.id = "dk.yumex.Yumex.Locale"
    assert flatpak_package.type == FlatpakType.LOCALE


def test_fppackage_appdata_notfound(flatpak_package):
    flatpak_package.ref.name = None
    assert flatpak_package.name == "Yumex"
    flatpak_package.ref.version = None
    assert flatpak_package.version == ""
    flatpak_package.ref.summary = None
    assert flatpak_package.summary == ""
