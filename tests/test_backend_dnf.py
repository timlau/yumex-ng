from datetime import datetime  # noqa: F401
from unittest.mock import patch, call


@patch("yumex.backend.dnf.Gio.Settings")
def test_reload_metadata_expired(mock_settings):
    mock_settings().get_int64.return_value = int(datetime.now().timestamp())
    mock_settings().get_int.return_value = 3600
    from yumex.backend.dnf import reload_metadata_expired

    res = reload_metadata_expired()
    assert not res


@patch("yumex.backend.dnf.Gio.Settings")
def test_reload_metadata_expired_is_expired(mock_settings):
    mock_settings().get_int64.return_value = int(datetime.now().timestamp())
    mock_settings().get_int.return_value = -1
    from yumex.backend.dnf import reload_metadata_expired

    res = reload_metadata_expired()
    assert res


@patch("yumex.backend.dnf.datetime")
@patch("yumex.backend.dnf.Gio.Settings")
def test_update_metadata_timestamp(mock_settings, mock_datetime):
    mock_datetime.now().timestamp.return_value = 10
    from yumex.backend.dnf import update_metadata_timestamp

    update_metadata_timestamp()
    assert call("dk.yumex.Yumex") in mock_settings.mock_calls
    assert call().set_int64("meta-load-time", 10) in mock_settings.mock_calls
