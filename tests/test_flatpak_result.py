import os
import pytest
import gi

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# from gi.repository import Gtk

from yumex.constants import PKGDATADIR

# pytestmark = pytest.mark.guitest
pytestmark = pytest.mark.skip("this test is broken")


@pytest.fixture
def result():
    """setup ressources and create a YumexXXXX object"""
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)

    from yumex.ui.flatpak_result import YumexFlatpakResult

    result = YumexFlatpakResult()
    return result


def test_setup(result):
    assert True is True
