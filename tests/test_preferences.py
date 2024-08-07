import gi
import pytest

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk
from yumex.utils.enums import FlatpakLocation
from .mock import mock_presenter, mock_gio_settings, TemplateUIFromFile

pytestmark = pytest.mark.guitest


@pytest.fixture
def pref(mocker, monkeypatch):
    """create a YumexPreferences object"""
    monkeypatch.setattr(Gtk, "Template", TemplateUIFromFile)
    from yumex.ui.preferences import YumexPreferences

    mock = mocker.patch("yumex.ui.preferences.Gio")
    mock.Settings.return_value = mock_gio_settings()
    presenter = mock_presenter(
        [
            "flathub",
            "gnome-nightly",
        ]
    )
    return YumexPreferences(presenter=presenter)


@pytest.fixture
def pref_no(mocker, monkeypatch):
    """create a YumexPreferences object"""
    monkeypatch.setattr(Gtk, "Template", TemplateUIFromFile)
    from yumex.ui.preferences import YumexPreferences

    mock = mocker.patch("yumex.ui.preferences.Gio")
    mock.Settings.return_value = mock_gio_settings()
    presenter = mock_presenter([])
    return YumexPreferences(presenter=presenter)


def test_get_current_location(pref):
    """should return the current selected installaton location"""
    assert pref.get_current_location() == FlatpakLocation.USER


def test_update_remote(pref):
    """should select the remote from the settings as active"""
    assert pref.update_remote(FlatpakLocation.USER) == "flathub"


def test_update_remote_not_found(pref):
    """should return the first remote available, if the one in settings don't exist"""
    pref.presenter.flatpak_backend.get_remotes.return_value = [
        "fedora",
        "fedora-updates",
    ]
    assert pref.settings.get_string("fp-remote") == "flathub"
    assert pref.update_remote(FlatpakLocation.USER) == "fedora"


def test_update_remote_no_remotes(pref_no):
    """should not select anything if not remotes exits for location"""
    assert pref_no.settings.get_string("fp-remote") == "flathub"
    assert pref_no.update_remote(FlatpakLocation.USER) is None


def test_get_current_remote(pref):
    """should return the current selected remote"""
    assert pref.get_current_remote() == "flathub"


def test_save_settings(pref):
    """should save the current settings (location and remote)"""
    location, remote = pref.save_settings()
    assert location == "user"
    assert remote == "flathub"
    assert pref.settings.set_string.call_count == 3
    pref.settings.set_string.assert_any_call("fp-location", "user")
    pref.settings.set_string.assert_any_call("fp-remote", "flathub")
    pref.settings.set_string.assert_any_call("upd-custom", "")
    print(pref.settings.mock_calls)
    assert pref.settings.set_boolean.call_count == 2
    pref.settings.set_boolean.assert_any_call("upd-show-icon", False)
    pref.settings.set_boolean.assert_any_call("upd-notification", False)
    assert pref.settings.set_int.call_count == 2
    pref.settings.set_int.assert_any_call("meta-load-periode", 3600)
    pref.settings.set_int.assert_any_call("upd-interval", 3600)


def test_save_settings_no_remotes(pref_no):
    """should only save location if there are no remotes"""
    location, remote = pref_no.save_settings()
    assert location == "user"
    assert remote is None
    assert pref_no.settings.set_string.call_count == 2
    pref_no.settings.set_string.assert_any_call("fp-location", "user")
    pref_no.settings.set_string.assert_any_call("upd-custom", "")


def test_setup(pref):
    """should setup the initial selected location and remote"""
    remote_selected = pref.fp_remote.get_selected_item()
    location_selected = pref.fp_location.get_selected_item()
    assert remote_selected is not None
    assert location_selected is not None
    assert remote_selected.get_string() == "flathub"
    assert location_selected.get_string() == FlatpakLocation.USER.value


def test_get_remotes(pref):
    """Should create a list of remote from the backemd"""
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
    """Should return an empty list if no remotes"""
    remotes = pref_no.get_remotes(FlatpakLocation.USER)
    assert isinstance(remotes, Gtk.StringList)
    assert len(remotes) == 0


def test_on_location_selected(pref):
    """Check the on_location_selected method"""
    pref.on_location_selected(widget=None, data=None)
    assert pref.fp_location.get_selected_item().get_string() == FlatpakLocation.USER
    pref.fp_location.set_selected(1)
    assert pref.fp_location.get_selected_item().get_string() == FlatpakLocation.SYSTEM


def test_on_location_selected_no_remotes(pref_no):
    """Check the on_location_selected method with no remotes available"""
    pref_no.on_location_selected(widget=None, data=None)
    location = pref_no.fp_location.get_selected_item().get_string()
    assert location == FlatpakLocation.USER

    """test on_remote_selected when there are no remotes"""
    remotes = pref_no.presenter.flatpak_backend.get_remotes(location=FlatpakLocation.USER)
    assert remotes == []
    assert pref_no.fp_remote.get_selected_item() is None
    assert pref_no.fp_remote.get_sensitive() is False
