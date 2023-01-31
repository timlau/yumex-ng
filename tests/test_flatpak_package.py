import gi

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

import pytest
from gi.repository import Flatpak
from yumex.utils.enums import FlatpakLocation, FlatpakType
from yumex.backend.flatpak import FlatpakPackage
from unittest.mock import MagicMock

pytestmark = pytest.mark.guitest


@pytest.fixture
def flatpak_ref():
    """create a fixture imulating a flatpak"""
    mock = MagicMock()
    mock.get_name.return_value = "dk.yumex.Yumex"
    mock.get_appdata_name.return_value = "Yum Extender"
    mock.get_appdata_version.return_value = "4.99"
    mock.get_appdata_summary.return_value = "This is a package manager"
    mock.format_ref.return_value = "app/dk.yumex.Yumex/x86_64/stable"
    mock.get_origin.return_value = "flathub"
    mock.get_kind.return_value = Flatpak.RefKind.APP
    return mock


@pytest.fixture
def flatpak_ref_no_appdata():
    """create a fixture imulating a flatpak with no appdata"""
    mock = MagicMock()
    mock.get_name.return_value = "dk.yumex.Yumex"
    mock.get_appdata_name.return_value = None
    mock.get_appdata_version.return_value = None
    mock.get_appdata_summary.return_value = None
    mock.format_ref.return_value = "app/dk.yumex.Yumex/x86_64/stable"
    mock.get_origin.return_value = "flathub"
    mock.get_kind.return_value = Flatpak.RefKind.APP
    return mock


@pytest.fixture
def flatpak_package(flatpak_ref):
    """create a fixture returning a flatpak package"""
    return FlatpakPackage(flatpak_ref, location=FlatpakLocation.USER)


def test_fppackage_id(flatpak_package):
    """should return the id of the flatpak"""
    assert flatpak_package.id == "dk.yumex.Yumex"


def test_fppackage_name(flatpak_package):
    """should return the name of the flatpak"""
    assert flatpak_package.name == "Yum Extender"


def test_fppackage_version(flatpak_package):
    """should return the version of the flatpak"""
    assert flatpak_package.version == "4.99"


def test_fppackage_summary(flatpak_package):
    """should return the summary of the flatpak"""
    assert flatpak_package.summary == "This is a package manager"


def test_fppackage_origin(flatpak_package):
    """should return the origin of the flatpak"""
    assert flatpak_package.origin == "flathub"


def test_fppackage_is_user(flatpak_package):
    """should return true if the flatpak is a user flatpak"""
    assert flatpak_package.is_user is True
    flatpak_package.location = FlatpakLocation.SYSTEM
    assert flatpak_package.is_user is False


def test_fppackage_repr(flatpak_package):
    """should the full ref string as a repr()"""
    assert repr(flatpak_package) == "app/dk.yumex.Yumex/x86_64/stable"


def test_fppackage_type(flatpak_ref):
    """Should return the type of the flatpak, based on Refkind or name"""
    flatpak_package = FlatpakPackage(flatpak_ref, location=FlatpakLocation.USER)
    assert flatpak_package.type == FlatpakType.APP
    flatpak_ref.get_kind.return_value = Flatpak.RefKind.RUNTIME
    flatpak_package = FlatpakPackage(flatpak_ref, location=FlatpakLocation.USER)
    assert flatpak_package.type == FlatpakType.RUNTIME
    flatpak_ref.get_name.return_value = "dk.yumex.Yumex.Locale"
    flatpak_package = FlatpakPackage(flatpak_ref, location=FlatpakLocation.USER)
    assert flatpak_package.type == FlatpakType.LOCALE


def test_fppackage_appdata_notfound(flatpak_ref_no_appdata):
    """Should name based on last part of id, if no appdata"""
    flatpak_package = FlatpakPackage(
        flatpak_ref_no_appdata, location=FlatpakLocation.USER
    )
    assert flatpak_package.name == "Yumex"
    assert flatpak_package.version == ""
    assert flatpak_package.summary == ""
