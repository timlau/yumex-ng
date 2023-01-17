from dataclasses import dataclass
import pytest
import os
import gi
from gi.repository import Gio
from yumex.constants import PKGDATADIR
from yumex.utils.enums import FlatpakLocation

pytestmark = pytest.mark.guitest


class MockWindow:
    def __init__(self):
        self._calls = []

    def set_needs_attention(self, *args, **kwargs):
        self._calls.append((__name__, args, kwargs))


class MockFlatpackBackend:
    def __init__(self, *args, **kwargs):
        self._calls = {}

    def get_mock_call(self, method) -> list:
        return self._calls.get(method, [])

    def set_mock_call(self, method, args, kwargs):
        call_list = self._calls.get(method, [])
        call_list.append((args, kwargs))
        self._calls[method] = call_list

    def get_installed(self, *args, **kwargs):
        self.set_mock_call("get_installed", args, kwargs)
        return []


@dataclass
class MockFlatpakPackage:
    id: str = "org.gnome.design.Contrast"


@pytest.fixture(autouse=True)
def mock_backend(monkeypatch):
    """use a mock backend"""
    monkeypatch.setattr(
        "yumex.backend.flatpak.backend.FlatpakBackend", MockFlatpackBackend
    )


@pytest.fixture
def window():
    """use a mock window"""
    return MockWindow()


@pytest.fixture
def flatpak_view(window):
    """setup ressources and create a YumexFlatpakView object"""
    gi.require_version("Flatpak", "1.0")
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)
    from yumex.ui.flatpak_view import YumexFlatpakView

    fpw: YumexFlatpakView = YumexFlatpakView(window)
    return fpw


@pytest.fixture
def package():
    return MockFlatpakPackage()


def test_backend_mock(flatpak_view):
    """Test that the backend is mocked."""
    assert isinstance(flatpak_view.backend, MockFlatpackBackend)


def test_backend_get_installed_called(flatpak_view):
    """Test that the backend, get_installed is called"""
    assert isinstance(flatpak_view.backend, MockFlatpackBackend)
    calls = flatpak_view.backend.get_mock_call("get_installed")
    assert len(calls) == 1
    assert calls[0] == ((), {"location": FlatpakLocation.BOTH})


def test_get_icon_paths(flatpak_view):
    assert isinstance(flatpak_view.backend, MockFlatpackBackend)
    paths = flatpak_view.get_icon_paths()
    for path in paths:
        assert "/icons/" in path


def test_find_icon(flatpak_view, package):
    # if org.gnome.design.Contrast is install we get a path
    path = flatpak_view.find_icon(package)
    if path:
        assert package.id in path
    notfound = MockFlatpakPackage(id="xx.xxxxxx.notfound")
    path = flatpak_view.find_icon(notfound)
    assert path is None
