from dataclasses import dataclass
import pytest
import os
import gi
from gi.repository import Gio
from yumex.constants import PKGDATADIR

pytestmark = pytest.mark.guitest


class MockWindow:
    def __init__(self):
        self._calls = []

    def set_needs_attention(self, *args, **kwargs):
        self._calls.append((__name__, args, kwargs))


@dataclass
class MockFlatpakPackage:
    id: str = "org.gnome.design.Contrast"


@pytest.fixture
def setup_resources():
    gi.require_version("Flatpak", "1.0")
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)
    return resource


@pytest.fixture
def window():
    return MockWindow()


@pytest.fixture
def package():
    return MockFlatpakPackage()


def test_get_icon_paths(setup_resources, window):
    from yumex.ui.flatpak_view import YumexFlatpakView

    fpw: YumexFlatpakView = YumexFlatpakView(window)
    paths = fpw.get_icon_paths()
    for path in paths:
        assert "/icons/" in path


def test_find_icon(setup_resources, window, package):
    from yumex.ui.flatpak_view import YumexFlatpakView

    fpw: YumexFlatpakView = YumexFlatpakView(window)
    # if org.gnome.design.Contrast is install we get a path
    path = fpw.find_icon(package)
    if path:
        assert package.id in path
    notfound = MockFlatpakPackage(id="xx.xxxxxx.notfound")
    path = fpw.find_icon(notfound)
    assert path is None
