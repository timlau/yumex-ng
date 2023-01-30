import gi

from yumex.utils.enums import FlatpakLocation, Page


gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from dataclasses import dataclass
import pytest
import os
from yumex.constants import PKGDATADIR
from .mock import mock_presenter

pytestmark = pytest.mark.guitest


@dataclass
class MockFlatpakPackage:
    id: str = "org.gnome.design.Contrast"


@pytest.fixture
def presenter():
    """use a mock window"""
    return mock_presenter()


@pytest.fixture
def flatpak_view(presenter):
    """setup ressources and create a YumexFlatpakView object"""
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)
    from yumex.ui.flatpak_view import YumexFlatpakView

    fpw: YumexFlatpakView = YumexFlatpakView(presenter=presenter)
    return fpw


@pytest.fixture
def package():
    return MockFlatpakPackage()


def test_backend_set_needs_attention(flatpak_view):
    """Test that the win.set_needs_attention is called with one update"""
    flatpak_view.presenter.set_needs_attention.assert_called()


def test_backend_get_installed_called(flatpak_view):
    """Test that backend,get_installed is called"""
    flatpak_view.backend.get_installed.assert_called_with(location=FlatpakLocation.BOTH)


def test_get_icon_paths(flatpak_view):
    paths = flatpak_view.get_icon_paths()
    assert "/icons/" in paths[0]


def test_find_icon(flatpak_view, package):
    # if org.gnome.design.Contrast is install we get a path
    path = flatpak_view.find_icon(package)
    if path:
        assert package.id in path
    notfound = MockFlatpakPackage(id="xx.xxxxxx.notfound")
    path = flatpak_view.find_icon(notfound)
    assert path is None


# def test_view_do_transaction(flatpak_view):
#     """Test that backend,install is called"""
#     flatpak_view.do_transaction(flatpak_view.backend.install, None)
#     assert flatpak_view.backend.get_number_of_calls() == 2
