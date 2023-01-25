import gi

from yumex.backend.flatpak import FlatpakPackage
from yumex.utils.enums import FlatpakLocation, Page

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


class MockPresenter(Mock):
    def __init__(self, fp_backend=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if fp_backend is None:
            fp_backend = MockFlatpackBackend()
        self._fp_backend = fp_backend

    def hide(self):
        self.set_mock_call("progress.hide")

    def reset_flatpak_backend(self):
        self.set_mock_call("reset_flatpak_backend")

    @property
    def flatpak_backend(self):
        return self._fp_backend

    def show_message(self, title, timeout=2) -> None:
        self.set_mock_call("show_message", title, timeout)

    def set_needs_attention(self, page: Page, num: int) -> None:
        self.set_mock_call("set_needs_attention", page, num)

    def confirm_flatpak_transaction(self, refs: list) -> bool:
        self.set_mock_call("confirm_flatpak_transaction", refs)
        return True

    def select_page(self, page: Page) -> None:
        self.set_mock_call("select_page", page)

    def get_repositories(self) -> list[tuple[str, str, bool]]:
        return [("fedora", "fedora packages", True)]


class MockFlatpackBackend(Mock):
    def __init__(self, remotes=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if remotes is None:
            remotes = ["flathub", "gnome-nightly"]
        self._remotes = remotes

    def get_installed(self, *args, **kwargs):
        self.set_mock_call("get_installed", *args, **kwargs)
        return [
            FlatpakPackage(
                MockFlatpakRef(), location=FlatpakLocation.USER, is_update=True
            )
        ]

    def install(self, *args, **kwargs):
        self.set_mock_call("install", *args, **kwargs)
        return [
            FlatpakPackage(
                MockFlatpakRef(), location=FlatpakLocation.USER, is_update=True
            )
        ]

    def number_of_updates(self):
        return 1

    def get_remotes(self, location: FlatpakLocation) -> list:
        return self._remotes


class MockSettings(Mock):
    def __init__(self, *args, **kwargs):
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
