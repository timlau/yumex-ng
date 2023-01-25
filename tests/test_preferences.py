import gi
import os

from yumex.constants import PKGDATADIR

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk
import pytest
from yumex.utils.enums import FlatpakLocation
from .mock import Mock, MockFlatpackBackend, MockPresenter

pytestmark = pytest.mark.guitest


class MockSettings(Mock):
    def __init__(self):
        Mock.__init__(self)

    # setting Mock methods
    def get_string(self, setting):
        match setting:
            case "fp-location":
                return FlatpakLocation.USER
            case "fp-remote":
                return "flathub"

    def set_string(self, setting, value):
        self.set_mock_call("set_string", setting, value)


@pytest.fixture
def pref():
    """setup ressources and create a YumexFlatpakView object"""
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)
    from yumex.ui.preferences import YumexPreferences

    presenter = MockPresenter()
    return YumexPreferences(settings=MockSettings(), presenter=presenter)


@pytest.fixture
def pref_no():
    """setup ressources and create a YumexFlatpakView object"""
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)
    from yumex.ui.preferences import YumexPreferences

    fp_backend = MockFlatpackBackend(remotes=[])
    assert fp_backend._remotes == []
    presenter = MockPresenter(fp_backend=fp_backend)
    return YumexPreferences(settings=MockSettings(), presenter=presenter)


def test_setup(pref):
    """Check that the default flatpak location and remote are set correctly"""
    assert pref.fp_remote.get_selected_item().get_string() == "flathub"
    assert pref.fp_location.get_selected_item().get_string() == FlatpakLocation.USER
    assert pref.settings.get_number_of_calls() == 1
    calls = pref.settings.get_calls()
    assert calls[0] == "set_string(fp-remote,user)"


def test_get_remotes(pref):
    """Check the get_remotes method"""
    remotes = pref.get_remotes(FlatpakLocation.USER)
    assert isinstance(remotes, Gtk.StringList)
    assert len(remotes) == 2
    assert remotes[0].get_string() == "flathub"
    assert remotes[1].get_string() == "gnome-nightly"


def test_get_remotes_none(pref_no):
    """Check the get_remotes method with no remotes available"""
    remotes = pref_no.get_remotes(FlatpakLocation.USER)
    assert isinstance(remotes, Gtk.StringList)
    assert len(remotes) == 0


def test_on_location_selected(pref):
    """Check the on_location_selected method"""
    pref.on_location_selected(widget=None, data=None)
    assert pref.fp_location.get_selected_item().get_string() == FlatpakLocation.USER
    pref.fp_location.set_selected(1)
    assert pref.fp_location.get_selected_item().get_string() == FlatpakLocation.SYSTEM
    # assert pref.win.settings.get_mock_call("set_string") is not None
    # assert pref.win.settings._calls != {}


def test_on_location_selected_no_remotes(pref_no):
    """Check the on_location_selected method with no remotes available"""
    pref_no.on_location_selected(widget=None, data=None)
    location = pref_no.fp_location.get_selected_item().get_string()
    assert location == FlatpakLocation.USER


def test_on_remote_selected_no_remotes(pref_no):
    """test on_remote_selected when there are no remotes"""
    assert not (
        pref_no.presenter.flatpak_backend.get_remotes(location=FlatpakLocation.USER)
    )
    assert pref_no.fp_remote.get_selected_item() is None
    pref_no.on_remote_selected(widget=None, data=None)
    assert pref_no.fp_remote.get_sensitive() is False
