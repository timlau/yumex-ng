import gi

gi.require_version("Flatpak", "1.0")
# gi.require_version("Gtk", "4.0")
# gi.require_version("Adw", "1")

from gi.repository import Flatpak


class Mock:
    def __init__(self, *args, **kwargs):
        self._calls = {}

    def get_mock_call(self, method) -> list:
        return self._calls.get(method, None)

    def set_mock_call(self, method, args, kwargs):
        call_list = self._calls.get(method, [])
        call_list.append((args, kwargs))
        self._calls[method] = call_list


class MockFlatpakRef(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = "dk.yumex.Yumex"
        self.name = "Yum Extender"
        self.version = "4.99"
        self.summary = "This is a package manager"
        self.ref_string = "app/dk.yumex.Yumex/x86_64/stable"
        self.kind = Flatpak.RefKind.APP

    def get_name(self) -> str:
        return self.id

    def get_appdata_name(self) -> str:
        return self.name

    def get_appdata_version(self) -> str:
        return self.version

    def get_appdata_summary(self) -> str:
        return self.summary

    def format_ref(self):
        return self.ref_string

    def get_origin(self):
        return "flathub"

    def get_kind(self):
        return self.kind
