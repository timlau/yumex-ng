import pytest
from unittest.mock import Mock
from yumex.backend.cache import YumexPackageCache
from yumex.backend.presenter import YumexPresenter
from yumex.utils.enums import Page


@pytest.fixture
def presenter() -> YumexPresenter:
    mock_factory = Mock()
    mock_win = Mock()
    presenter = YumexPresenter(win=mock_win, factory=mock_factory)
    mock_factory.get_backend.return_value = Mock()
    return presenter


def test_package_backend(presenter: YumexPresenter):
    """test package_backend is only created once"""
    backend1 = presenter.package_backend
    backend2 = presenter.package_backend
    assert backend1 == backend2
    presenter.dnf_backend_factory.get_backend.assert_called_once()


def test_reset_package_backend(presenter: YumexPresenter):
    _ = presenter.package_backend
    presenter.reset_backend()
    _ = presenter.package_backend
    # because backend is resat, the factory.get_backend should be called twice
    assert presenter.dnf_backend_factory.get_backend.call_count == 2


def test_package_cache(presenter: YumexPresenter):
    """test package_cache is only created once"""
    cache1 = presenter.package_cache
    cache2 = presenter.package_cache
    assert cache1 == cache2
    assert isinstance(cache1, YumexPackageCache)


def test_reset_cache(presenter: YumexPresenter):
    cache1 = presenter.package_cache
    presenter.reset_cache()
    cache2 = presenter.package_cache
    assert cache1 != cache2


def test_flatpak_backend(presenter: YumexPresenter, mocker):
    """test flatpak_backend is only created once"""
    fp_init = mocker.patch("yumex.backend.presenter.FlatpakBackend")
    backend1 = presenter.flatpak_backend
    backend2 = presenter.flatpak_backend
    assert backend1 == backend2
    assert isinstance(backend1, Mock)
    assert fp_init.call_count == 1


def test_reset_flatpak_backend(presenter: YumexPresenter, mocker):
    """test flatpak_backend is only created once"""
    fp_init = mocker.patch(
        "yumex.backend.presenter.FlatpakBackend.__init__", return_value=None
    )
    _ = presenter.flatpak_backend
    presenter.reset_flatpak_backend()
    _ = presenter.flatpak_backend
    assert fp_init.call_count == 2


def test_get_main_window(presenter: YumexPresenter):
    win = presenter.get_main_window()
    assert isinstance(win, Mock)


def test_get_show_message(presenter: YumexPresenter):
    win = presenter.get_main_window()
    presenter.show_message("test", 4)
    win.show_message.assert_called_with("test", 4)


def test_set_needs_attention(presenter: YumexPresenter):
    win = presenter.get_main_window()
    presenter.set_needs_attention(Page.FLATPAKS, 4)
    win.set_needs_attention.assert_called_with(Page.FLATPAKS, 4)


def test_confirm_flatpak_transaction(presenter: YumexPresenter):
    win = presenter.get_main_window()
    presenter.confirm_flatpak_transaction([1, 2, 3])
    win.confirm_flatpak_transaction.assert_called_with([1, 2, 3])


def test_search(presenter: YumexPresenter):
    backend = presenter.package_backend
    presenter.search("test", None, 1)
    backend.search.assert_called_with("test", None, 1)


def test_get_package_info(presenter: YumexPresenter):
    backend = presenter.package_backend
    presenter.get_package_info(None, 1)
    backend.get_package_info.assert_called_with(None, 1)


def test_get_repositories(presenter: YumexPresenter):
    backend = presenter.package_backend
    presenter.get_repositories()
    backend.get_repositories.assert_called_once()


def test_depsolve(presenter: YumexPresenter):
    backend = presenter.package_backend
    presenter.depsolve([None, None, None])
    backend.depsolve.assert_called_with([None, None, None])
