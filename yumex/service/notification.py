# Send a notication using freedesktop Notification API
#
# https://specifications.freedesktop.org/notification-spec/latest/ar01s09.html

from dataclasses import dataclass
import logging
from typing import Callable
from dasbus.connection import SessionMessageBus
from dasbus.identifier import DBusServiceIdentifier
from dasbus.loop import EventLoop

logger = logging.getLogger("yumex_updater")

NOTIFICATION_NAMESPACE = ("org", "freedesktop", "Notifications")
NOTIFICATION = DBusServiceIdentifier(namespace=NOTIFICATION_NAMESPACE, message_bus=SessionMessageBus())


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
        proxy = NOTIFICATION.get_proxy()
        proxy.ActionInvoked.connect(self.on_action_invoked)

    @property
    def send_actions(self):
        res = []
        for action in self.actions.values():
            res.append(action.id)
            res.append(action.title)
        return res

    def send(self, summary, body, timeout=0):
        proxy = NOTIFICATION.get_proxy()
        id = proxy.Notify(self.app_name, 0, self.icon_name, summary, body, self.send_actions, self.hints, timeout)
        self.send_ids.append(id)

    def on_action_invoked(self, id, action_id):
        logger.info(f"SIGNAL:ActionInvoked id: {id} action: {action_id}")
        if action_id in self.actions:
            action = self.actions[action_id]
            action.callback(action_id)


def callback(*args):
    logger.debug(f"callback was called with : {args}")


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
    loop = EventLoop()
    loop.run()


if __name__ == "__main__":
    main()
