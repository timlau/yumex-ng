from dataclasses import dataclass

import gi
import pytest

from yumex.utils.enums import FlatpakLocation, Page

from .mock import TemplateUIFromFile, mock_presenter

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


from gi.repository import Gtk  # noqa: E402

pytestmark = pytest.mark.guitest


@dataclass
class MockFlatpakPackage:
    id: str = "org.gnome.design.Contrast"


@pytest.fixture
def presenter():
    """use a mock window"""
    return mock_presenter()


@pytest.fixture
def flatpak_view(presenter, monkeypatch):
    """setup ressources and create a YumexFlatpakView object"""
    # used the Special Gtk.Template wrapper
    monkeypatch.setattr(Gtk, "Template", TemplateUIFromFile)
    from yumex.ui.flatpak_view import YumexFlatpakView

    fpw: YumexFlatpakView = YumexFlatpakView(presenter=presenter)
    return fpw


@pytest.fixture
def package():
    return MockFlatpakPackage()


def test_backend_set_needs_attention(flatpak_view):
    """Test that the win.set_needs_attention is called with one update"""
    flatpak_view.presenter.set_needs_attention.assert_called_with(Page.FLATPAKS, 1)


def test_backend_get_installed_called(flatpak_view):
    """Test that backend,get_installed is called"""
    flatpak_view.backend.get_installed.assert_called_with(location=FlatpakLocation.BOTH)


def test_get_icon_paths(flatpak_view, monkeypatch):
    """check get_icon_paths()"""
    monkeypatch.setenv("XDG_DATA_DIRS", "/path1:/path2")
    paths = flatpak_view.get_icon_paths()
    assert paths[0] == "/path1/icons/"
    assert paths[1] == "/path2/icons/"
