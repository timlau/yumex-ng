import pytest
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk
from .mock import TemplateUIFromFile


@pytest.fixture
def progress(mocker, monkeypatch):
    """create a progress object"""
    # used the Special Gtk.Template wrapper
    monkeypatch.setattr(Gtk, "Template", TemplateUIFromFile)

    from yumex.ui.progress import YumexProgress

    progress = YumexProgress()
    return progress


def test_set_title(progress):
    progress.set_title("titel")
    assert progress.title.get_label() == "titel"


def test_set_subtitle(progress):
    progress.set_subtitle("subtitel")
    assert progress.subtitle.get_label() == "subtitel"
