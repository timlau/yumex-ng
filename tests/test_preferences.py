import gi
import os

from yumex.constants import PKGDATADIR

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk
import pytest
from yumex.utils.enums import FlatpakLocation
from .mock import Mock

pytestmark = pytest.mark.guitest


class MockSettings(Mock):
    def get_string(self, setting):
        match setting:
            case "fp-location":
                return FlatpakLocation.USER
            case "fp-remote":
                return "flathub"

    def set_string(self, setting, value):
        self.set_mock_call("set_string", setting, value)


class MockPackageBackend(Mock):
    def get_repositories(self) -> list[tuple[str, str, bool]]:
        return [("fedora", "fedora packages", True)]


class MockFlatpackBackend(Mock):
    def __init__(self, remotes):
        super().__init__()
        self._remotes = remotes

    def get_remotes(self, location: FlatpakLocation) -> list:
        return self._remotes


class MockPackageView(Mock):
    @property
    def backend(self):
        return MockPackageBackend()


class MockFlatpakView(Mock):
    def __init__(self, remotes):
        Mock.__init__(self)
        self._remotes = remotes

    @property
    def backend(self):
        return MockFlatpackBackend(self._remotes)


class MockWindow(Mock):
    def __init__(self, remotes):
        Mock.__init__(self)
        self._remotes = remotes

    @property
    def package_view(self):
        return MockPackageView()

    @property
    def flatpak_view(self):
        return MockFlatpakView(self._remotes)

    @property
    def settings(self):
        return MockSettings()


@pytest.fixture
def pref():
    """setup ressources and create a YumexFlatpakView object"""
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)
    from yumex.ui.preferences import YumexPreferences

    remotes = ["flathub", "gnome-nightly"]
    return YumexPreferences(win=MockWindow(remotes=remotes))


@pytest.fixture
def pref_no():
    """setup ressources and create a YumexFlatpakView object"""
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)
    from yumex.ui.preferences import YumexPreferences

    remotes = []
    return YumexPreferences(win=MockWindow(remotes=remotes))


def test_setup(pref):
    """Check that the default flatpak location and remote are set correctly"""
    assert pref.fp_remote.get_selected_item().get_string() == "flathub"
    assert pref.fp_location.get_selected_item().get_string() == FlatpakLocation.USER


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
        pref_no.win.flatpak_view.backend.get_remotes(location=FlatpakLocation.USER)
    )
    assert pref_no.fp_remote.get_selected_item() is None
    pref_no.on_remote_selected(widget=None, data=None)
    assert pref_no.fp_remote.get_sensitive() is False
