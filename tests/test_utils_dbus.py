import pytest  # noqa: F401
from unittest.mock import patch, call
from dasbus.error import DBusError

from tests.mock import Mock  # noqa


def test_is_user_service_running():
    from yumex.utils.dbus import is_user_service_running

    res = is_user_service_running("dconf.service")
    assert res
    res = is_user_service_running("notfound.service")
    assert not res


@patch("yumex.utils.dbus.SYSTEMD")
def test_is_user_service_running_mocked(mock_systemd):
    mock_systemd.get_proxy().Get.return_value = "running"
    mock_systemd.get_proxy().GetUnit.return_value = "/org/freedesktop/systemd1/unit/dconf_2eservice"
    from yumex.utils.dbus import is_user_service_running

    res = is_user_service_running("dconf.service")
    assert res
    calls = mock_systemd.mock_calls
    assert call.get_proxy(interface_name="org.freedesktop.systemd1.Manager") in calls
    assert call.get_proxy().GetUnit("dconf.service") in calls
    assert call.get_proxy("/org/freedesktop/systemd1/unit/dconf_2eservice") in calls
    assert call.get_proxy().Get("org.freedesktop.systemd1.Unit", "SubState") in calls


@patch("yumex.utils.dbus.SYSTEMD")
def test_is_user_service_not_running_mocked(mock_systemd):
    mock_systemd.get_proxy().Get.return_value = "dead"
    mock_systemd.get_proxy().GetUnit.return_value = "/org/freedesktop/systemd1/unit/dconf_2eservice"
    from yumex.utils.dbus import is_user_service_running

    res = is_user_service_running("dconf.service")
    assert not res
    calls = mock_systemd.mock_calls
    assert call.get_proxy(interface_name="org.freedesktop.systemd1.Manager") in calls
    assert call.get_proxy().GetUnit("dconf.service") in calls
    assert call.get_proxy("/org/freedesktop/systemd1/unit/dconf_2eservice") in calls
    assert call.get_proxy().Get("org.freedesktop.systemd1.Unit", "SubState") in calls


@patch("yumex.utils.dbus.AsyncDbusCaller")
@patch("yumex.utils.dbus.is_user_service_running")
def test_sync_updates_not_running(mock_is_user_service_running, mock_async):
    mock_is_user_service_running.return_value = False
    from yumex.utils.dbus import sync_updates

    res, msg = sync_updates()
    assert not res
    assert msg == "yumex-updater-systray not running"


@patch("yumex.utils.dbus.AsyncDbusCaller")
@patch("yumex.utils.dbus.YUMEX_UPDATER")
@patch("yumex.utils.dbus.is_user_service_running")
def test_sync_updates_running(mock_is_user_service_running, mock_yumex_updater, mock_async):
    mock_is_user_service_running.return_value = True
    from yumex.utils.dbus import sync_updates

    res, msg = sync_updates()
    assert res
    assert msg == "RefreshUpdates triggered"
    mock_yumex_updater.get_proxy.assert_called_once()
    assert call().call(mock_yumex_updater.get_proxy().RefreshUpdates, False) in mock_async.mock_calls


@patch("yumex.utils.dbus.AsyncDbusCaller")
@patch("yumex.utils.dbus.YUMEX_UPDATER")
@patch("yumex.utils.dbus.is_user_service_running")
def test_sync_updates_error(mock_is_user_service_running, mock_yumex_updater, mock_async):
    mock_is_user_service_running.return_value = True
    mock_yumex_updater.get_proxy.side_effect = DBusError
    from yumex.utils.dbus import sync_updates

    res, msg = sync_updates()
    assert not res
    assert msg == "DBusError : "
