from unittest.mock import patch, call, Mock
from dasbus.error import DBusError


class MockASyncCaller:
    def __init__(self) -> None:
        pass

    def call(self, mth, *args, **kwargs):
        return mth(*args, **kwargs)


def test_async_caller_timeout():
    from yumex.utils.dbus import AsyncDbusCaller

    def raise_timeout():
        raise TimeoutError

    async_caller = AsyncDbusCaller()
    async_caller.loop = Mock()
    async_caller.callback(raise_timeout)
    assert async_caller.res == "DBus Timeout error"


def test_async_caller_dbuserror_peer_disconnect():
    from yumex.utils.dbus import AsyncDbusCaller

    def raise_dbus_error():
        raise DBusError("Remote peer disconnected")

    async_caller = AsyncDbusCaller()
    async_caller.loop = Mock()
    async_caller.callback(raise_dbus_error)
    assert async_caller.res is None


def test_async_caller_dbuserror_polkit_auth_timeout():
    from yumex.utils.dbus import AsyncDbusCaller

    def raise_dbus_error():
        raise DBusError("Method call timed out")

    async_caller = AsyncDbusCaller()
    async_caller.loop = Mock()
    async_caller.callback(raise_dbus_error)
    assert async_caller.res == "PolicyKit Autherisation failed"


def test_async_caller_dbuserror_polkit_auth_cancel():
    from yumex.utils.dbus import AsyncDbusCaller

    def raise_dbus_error():
        raise DBusError("Not authorized")

    async_caller = AsyncDbusCaller()
    async_caller.loop = Mock()
    async_caller.callback(raise_dbus_error)
    assert async_caller.res == "PolicyKit Autherisation failed"


def test_async_caller_dbuserror_unknown():
    from yumex.utils.dbus import AsyncDbusCaller

    def raise_dbus_error():
        raise DBusError("This error is unknown")

    async_caller = AsyncDbusCaller()
    async_caller.loop = Mock()
    async_caller.callback(raise_dbus_error)
    assert async_caller.res is None


def test_is_user_service_running():
    from yumex.utils.dbus import is_user_service_running

    res = is_user_service_running("notfound.service")
    assert not res


@patch("yumex.utils.dbus.AsyncDbusCaller")
@patch("yumex.utils.dbus.SYSTEMD")
def test_is_user_service_running_mocked(mock_systemd, mock_async):
    mock_async.return_value = MockASyncCaller()
    mock_systemd.get_proxy().Get.return_value = "running"
    mock_systemd.get_proxy().GetUnit.return_value = "/org/freedesktop/systemd1/unit/dconf_2eservice"
    from yumex.utils.dbus import is_user_service_running

    res = is_user_service_running("dconf.service")
    assert res
    assert call.get_proxy(interface_name="org.freedesktop.systemd1.Manager") in mock_systemd.mock_calls
    assert call.get_proxy().GetUnit("dconf.service") in mock_systemd.mock_calls
    assert call.get_proxy("/org/freedesktop/systemd1/unit/dconf_2eservice") in mock_systemd.mock_calls
    assert call.get_proxy().Get("org.freedesktop.systemd1.Unit", "SubState") in mock_systemd.mock_calls


@patch("yumex.utils.dbus.AsyncDbusCaller")
@patch("yumex.utils.dbus.SYSTEMD")
def test_is_user_service_not_running_mocked(mock_systemd, mock_async):
    mock_async.return_value = MockASyncCaller()
    mock_systemd.get_proxy().Get.return_value = "dead"
    mock_systemd.get_proxy().GetUnit.return_value = "/org/freedesktop/systemd1/unit/dconf_2eservice"
    from yumex.utils.dbus import is_user_service_running

    res = is_user_service_running("dconf.service")
    assert not res
    assert call.get_proxy(interface_name="org.freedesktop.systemd1.Manager") in mock_systemd.mock_calls
    assert call.get_proxy().GetUnit("dconf.service") in mock_systemd.mock_calls
    assert call.get_proxy("/org/freedesktop/systemd1/unit/dconf_2eservice") in mock_systemd.mock_calls
    assert call.get_proxy().Get("org.freedesktop.systemd1.Unit", "SubState") in mock_systemd.mock_calls


@patch("yumex.utils.dbus.AsyncDbusCaller")
@patch("yumex.utils.dbus.is_user_service_running")
def test_sync_updates_not_running(mock_is_user_service_running, mock_async):
    mock_async.return_value = MockASyncCaller()
    mock_is_user_service_running.return_value = False
    from yumex.utils.dbus import sync_updates

    res, msg = sync_updates()
    assert not res
    assert msg == "yumex-updater-systray not running"


@patch("yumex.utils.dbus.AsyncDbusCaller")
@patch("yumex.utils.dbus.YUMEX_UPDATER")
@patch("yumex.utils.dbus.is_user_service_running")
def test_sync_updates_running(mock_is_user_service_running, mock_yumex_updater, mock_async):
    mock_async.return_value = MockASyncCaller()
    mock_is_user_service_running.return_value = True
    from yumex.utils.dbus import sync_updates

    res, msg = sync_updates()
    print(mock_yumex_updater.mock_calls)
    assert res
    assert msg == "RefreshUpdates triggered"
    assert call.get_proxy().RefreshUpdates(False) in mock_yumex_updater.mock_calls


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
