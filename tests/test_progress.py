import os
import pytest
import gi

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk

from yumex.constants import PKGDATADIR

pytestmark = pytest.mark.guitest


@pytest.fixture
def progress():
    """setup ressources and create a YumexFlatpakView object"""
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)
    from yumex.ui.progress import YumexProgress

    progress = YumexProgress()
    return progress


def test_setup(progress):
    assert isinstance(progress.title, Gtk.Label)
    assert isinstance(progress.subtitle, Gtk.Label)
    assert isinstance(progress.progress, Gtk.ProgressBar)
    assert isinstance(progress.spinner, Gtk.Spinner)
