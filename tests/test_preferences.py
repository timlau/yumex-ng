import gi
import os

from yumex.constants import PKGDATADIR

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk
import pytest
from yumex.utils.enums import FlatpakLocation
from .mock import mock_presenter, mock_settings

pytestmark = pytest.mark.guitest


@pytest.fixture
def pref(mocker):
    """setup ressources and create a YumexFlatpakView object"""
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)
    from yumex.ui.preferences import YumexPreferences

    mock = mocker.patch("yumex.ui.preferences.Gio")
    mock.Settings.return_value = mock_settings()
    presenter = mock_presenter(
        [
            "flathub",
            "gnome-nightly",
        ]
    )
    return YumexPreferences(presenter=presenter)


@pytest.fixture
def pref_no(mocker):
    """setup ressources and create a YumexFlatpakView object"""
    from gi.repository import Gio

    resource = Gio.Resource.load(os.path.join(PKGDATADIR, "yumex.gresource"))
    Gio.Resource._register(resource)
    from yumex.ui.preferences import YumexPreferences

    mock = mocker.patch("yumex.ui.preferences.Gio")
    mock.Settings.return_value = mock_settings()
    presenter = mock_presenter([])
    return YumexPreferences(presenter=presenter)


def test_mock_settings(pref):
    assert pref.settings.get_string("fp-location") == FlatpakLocation.USER
    assert pref.settings.get_string("fp-remote") == "flathub"


def test_get_current_location(pref):
    assert pref.get_current_location() == FlatpakLocation.USER


def test_update_remote(pref):
    assert pref.update_remote(FlatpakLocation.USER) == "flathub"


def test_update_remote_not_found(pref):
    pref.presenter.flatpak_backend.get_remotes.return_value = [
        "fedora",
        "fedora-updates",
    ]
    assert pref.settings.get_string("fp-remote") == "flathub"
    assert pref.update_remote(FlatpakLocation.USER) == "fedora"


def test_update_remote_no_remotes(pref_no):
    assert pref_no.settings.get_string("fp-remote") == "flathub"
    assert pref_no.update_remote(FlatpakLocation.USER) is None


def test_get_current_remote(pref):
    assert pref.get_current_remote() == "flathub"


def test_save_settings(pref):
    """test save setting"""
    location, remote = pref.save_settings()
    assert location == "user"
    assert remote == "flathub"
    assert pref.settings.set_string.call_count == 2
    pref.settings.set_string.assert_any_call("fp-location", "user")
    pref.settings.set_string.assert_any_call("fp-remote", "flathub")


def test_save_settings_no_remotes(pref_no):
    """test save settins with no remotes, fp-remote will not be written"""
    location, remote = pref_no.save_settings()
    assert location == "user"
    assert remote is None
    assert pref_no.settings.set_string.call_count == 1
    pref_no.settings.set_string.called_with("fp-location", "user")


def test_setup(pref):
    """Check that the default flatpak location and remote are set correctly"""
    # assert pref.fp_remote.get_selected_item() is not None
    remote_selected = pref.fp_remote.get_selected_item()
    location_selected = pref.fp_location.get_selected_item()
    assert remote_selected is not None
    assert location_selected is not None
    assert remote_selected.get_string() == "flathub"
    assert location_selected.get_string() == FlatpakLocation.USER.value
    # assert pref.settings.set_string.assert_called_with(
    #     "fp-location", FlatpakLocation.USER
    # )


def test_get_remotes(pref):
    """Check the get_remotes method"""
    pref.presenter.flatpak_backend.get_remotes.return_value = [
        "flathub",
        "gnome-nightly",
    ]
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

    """test on_remote_selected when there are no remotes"""
    remotes = pref_no.presenter.flatpak_backend.get_remotes(
        location=FlatpakLocation.USER
    )
    assert remotes == []
    assert pref_no.fp_remote.get_selected_item() is None
    assert pref_no.fp_remote.get_sensitive() is False
