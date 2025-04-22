import sys
from unittest.mock import MagicMock

import gi
import pytest

import yumex.utils
from yumex.utils.enums import (
    InfoType,
    PackageFilter,
    SortType,
)

from .mock import TemplateUIFromFile, dummy_package

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk  # noqa: E402


def translate(text):
    return text


# add a dummy _() method to global namespace as fake translation function
sys.modules["builtins"].__dict__["_"] = translate


def mock_presenter():
    """Mock the presenter"""
    mock = MagicMock()
    mock.get_packages_by_filter.return_value = [dummy_package()]
    mock.search.return_value = [dummy_package()]
    # dont use cache, just return the same packages
    mock.get_packages.side_effect = lambda x: x
    return mock


def mock_win():
    """mock the main window"""
    mock = MagicMock()
    # mock the package_setting method call by YumexPackageView
    mock.package_settings.get_sort_attr.return_value = SortType.NAME
    mock.package_settings.get_info_type.return_value = InfoType.DESCRIPTION
    return mock


def mock_queueview():
    """mock the queueview"""
    mock = MagicMock()
    mock.find_by_nevra.return_value = None
    return mock


def run_sync(func, callback, *args, **kwargs):
    """replacement for RunAsync, that dont work well with testing"""
    res = func(*args, **kwargs)
    return callback(res)


@pytest.fixture
def view(monkeypatch, mocker):
    """create a YumexPackageView object"""
    # used the Special Gtk.Template wrapper
    monkeypatch.setattr(Gtk, "Template", TemplateUIFromFile)
    monkeypatch.setattr(yumex.utils, "RunAsync", run_sync)

    from yumex.ui.package_view import YumexPackageView

    presenter = mock_presenter()
    queue_view = mock_queueview()
    view = YumexPackageView(presenter=presenter, qview=queue_view)
    return view


def test_add_packages_to_store(view):
    """should add the package to the view storage"""
    pkgs = [dummy_package()]
    view.add_packages_to_store(pkgs)
    assert len(view.storage) == 1


def test_add_packages_to_store_empty(view):
    """should add the package to the view storage"""
    pkgs = []
    view.add_packages_to_store(pkgs)
    assert len(view.storage) == 0


def test_get_packages(view):
    """should get one package and add it to the view storage"""
    view.get_packages(PackageFilter.INSTALLED)
    assert len(view.storage) == 1


def test_get_packages_empty(view):
    """should not get anything"""
    view.presenter.get_packages_by_filter.return_value = []
    view.get_packages(PackageFilter.INSTALLED)
    assert len(view.storage) == 0


def test_search(view):
    """should get one package and add it to the view storage"""
    view.search("text")
    assert len(view.storage) == 1


def test_search_empty(view):
    """should not find anything"""
    view.presenter.search.return_value = []
    view.search("text")
    assert len(view.storage) == 0


def test_search_2chars(view):
    """should not do a search with less than 3 characters"""
    view.search("12")
    assert len(view.storage) == 0


def test_select_all(view):
    view.get_packages(PackageFilter.AVAILABLE)
    # all packages are selected and added to queue
    assert len(view.storage) == 1
    to_add, to_delete = view.select_all(state=True)
    assert len(to_add) == 1
    assert len(to_delete) == 0
    view.queue_view.add_packages.assert_called_with(to_add)
    # all packages are de-selected and removed from queue
    to_add, to_delete = view.select_all(state=False)
    assert len(to_add) == 0
    assert len(to_delete) == 1
    view.queue_view.remove_packages.assert_called_with(to_delete)
