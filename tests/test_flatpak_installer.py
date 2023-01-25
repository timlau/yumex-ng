import os
import pytest
import gi

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# from gi.repository import Gtk

from yumex.constants import PKGDATADIR
from .mock import MockPresenter, MockSettings

# pytestmark = pytest.mark.guitest
pytestmark = pytest.mark.skip("this test is broken")


@pytest.fixture
def installer(monkeypatch):
    """setup ressources and create a YumexXXXX object"""
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)

    from yumex.ui.flatpak_installer import YumexFlatpakInstaller

    monkeypatch.setattr(Gio, "Settings", MockSettings)
    presenter = MockPresenter()
    installer = YumexFlatpakInstaller(presenter=presenter)
    return installer


def test_setup(installer):
    assert True is True
