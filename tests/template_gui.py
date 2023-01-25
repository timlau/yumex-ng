import os
import pytest
import gi

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# from gi.repository import Gtk

from yumex.constants import PKGDATADIR

pytestmark = pytest.mark.guitest


@pytest.fixture
def YumexXXXX():
    """setup ressources and create a YumexXXXX object"""
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)

    # add import here for YumexXXXX
    # from yumex.ui.progress import YumexProgress

    xxxxx = YumexXXXX()
    return xxxxx


def test_setup(xxxxx):
    assert True is True
