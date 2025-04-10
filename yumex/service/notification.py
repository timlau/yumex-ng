# Send a notication using freedesktop Notification API
#
# https://specifications.freedesktop.org/notification-spec/latest/ar01s09.html

import logging
from dataclasses import dataclass
from typing import Callable

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

DBusGMainLoop(set_as_default=True)

logger = logging.getLogger("yumex_updater")


NOTIFICATION_BUS_NAME = "org.freedesktop.Notifications"
NOTIFICATION_OBJECT_PATH = "/" + NOTIFICATION_BUS_NAME.replace(".", "/")
bus = dbus.SessionBus()


@dataclass
class Action:
    id: str
    title: str
    callback: Callable


class Notification:
    def __init__(self, app_name, icon_name, actions: list[Action] = [], hints={}):
        self.send_ids = []
        self.app_name = app_name
        self.icon_name = icon_name
        self.actions: dict[str, Action] = {action.id: action for action in actions}
        self.hints = hints
        self.last_value = 0
        self.last_pkgs = 0
        self.last_flatpaks = 0
        self.iface_notification = dbus.Interface(
            bus.get_object(NOTIFICATION_BUS_NAME, NOTIFICATION_OBJECT_PATH), dbus_interface=NOTIFICATION_BUS_NAME
        )
        self.iface_notification.connect_to_signal("ActionInvoked", self.on_action_invoked)

    @property
    def send_actions(self):
        res = []
        for action in self.actions.values():
            res.append(action.id)
            res.append(action.title)
        return res

    def send(self, summary, body, timeout=0):
        id = self.iface_notification.Notify(
            self.app_name, 0, self.icon_name, summary, body, self.send_actions, self.hints, timeout
        )
        self.send_ids.append(id)

    def on_action_invoked(self, id, action_id):
        logger.info(f"SIGNAL:ActionInvoked id: {id} action: {action_id}")
        if action_id in self.actions:
            action = self.actions[action_id]
            action.callback(action_id, self.last_pkgs, self.last_flatpaks)


loop = None


def callback(*args):
    logger.debug(f"callback was called with : {args}")
    global loop
    loop.quit()


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="(%(name)-5s) -  %(message)s",
        datefmt="%H:%M:%S",
    )
    app_name = "Yum Extender"
    icon_name = "software-update-available-symbolic"
    summary = "Updates is available"
    body = "this is the body of the notifcation"
    action = [Action("open", "Open Yum Extender", callback)]
    notification = Notification(app_name, icon_name, actions=action)
    notification.send(summary, body)
    global loop
    loop = GLib.MainLoop()
    loop.run()


if __name__ == "__main__":
    main()
