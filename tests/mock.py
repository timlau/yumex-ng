from unittest.mock import MagicMock
import gi

from yumex.backend.flatpak import FlatpakPackage
from yumex.utils.enums import FlatpakLocation

gi.require_version("Flatpak", "1.0")
# gi.require_version("Gtk", "4.0")
# gi.require_version("Adw", "1")

from gi.repository import Flatpak


class Mock:
    def __init__(self, *args, **kwargs):
        self._calls = []

    def __getattr__(self, attr):
        """all unknown attributes, just return self"""
        self.set_mock_call(f"{attr}")
        return self

    def get_calls(self):
        return self._calls

    def get_number_of_calls(self):
        return len(self._calls)

    def get_mock_call(self, method) -> list:
        return [call for call in self._calls if call.startswith(method)]

    def set_mock_call(self, method, *args, **kwargs):
        param_str = ""
        if args:
            param_str += ",".join([str(elem) for elem in args])
        if kwargs:
            param_str += ",".join([f"{key}={value}" for key, value in kwargs.items()])
        if param_str:
            self._calls.append(f"{method}({param_str})")
        else:
            self._calls.append(f"{method}")


def flatpak_ref():
    mock = MagicMock()
    mock.get_name.return_value = "dk.yumex.Yumex"
    mock.get_appdata_name.return_value = "Yum Extender"
    mock.get_appdata_version.return_value = "4.99"
    mock.get_appdata_summary.return_value = "This is a package manager"
    mock.format_ref.return_value = "app/dk.yumex.Yumex/x86_64/stable"
    mock.get_origin.return_value = "flathub"
    mock.get_kind.return_value = Flatpak.RefKind.APP
    return mock


def mock_presenter(remotes: list = None):
    mock = MagicMock()
    mock.flatpak_backend.get_remotes.return_value = remotes
    mock.flatpak_backend.number_of_updates.return_value = 1
    mock.confirm_flatpak_transaction.return_value = True
    mock.get_repositories.return_value = [("fedora", "fedora packages", True)]
    fp_pkg = FlatpakPackage(
        flatpak_ref(), location=FlatpakLocation.USER, is_update=True
    )
    mock.get_installed.return_value = [fp_pkg]
    mock.install.return_value = [fp_pkg]
    mock.number_of_updates.return_value = 1
    return mock


def mock_settings():
    def get_string(setting):
        match setting:
            case "fp-location":
                return "user"
            case "fp-remote":
                return "flathub"

    mock = MagicMock()
    mock.get_string.side_effect = get_string
    return mock
