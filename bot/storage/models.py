import msgspec

from .enums import SubscriptionType

from datetime import datetime


class Subscriber(msgspec.Struct, frozen=True):
    chat_id: int
    user_id: int | None = None


class BotStorageData(msgspec.Struct):
    subscribers: dict[SubscriptionType, dict[int, set[Subscriber]]] = msgspec.field(
        default_factory=lambda: {SubscriptionType.TRIGGER: {}}
    )
    completed_background_tasks: dict[int, datetime] = {}


class ChatStorageData(msgspec.Struct):
    last_bot_message_ids: list[int] = []


class UserStorageData(msgspec.Struct):
    subscriptions: dict[SubscriptionType, set[int]] = msgspec.field(
        default_factory=lambda: {
            SubscriptionType.TRIGGER: set(),
            SubscriptionType.MESSAGE_KEYBOARD_BUTTON: set(),
        }
    )
    temporary_variables: dict[str, str] = {}
