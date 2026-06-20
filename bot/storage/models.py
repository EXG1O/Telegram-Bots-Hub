import msgspec

from datetime import datetime


class TriggerSubscriber(msgspec.Struct, frozen=True):
    chat_id: int
    user_id: int | None = None


class BotStorageData(msgspec.Struct):
    expected_triggers: dict[int, set[TriggerSubscriber]] = {}
    completed_background_tasks: dict[int, datetime] = {}


class ChatStorageData(msgspec.Struct):
    last_bot_message_ids: list[int] = []


class UserStorageData(msgspec.Struct):
    temporary_variables: dict[str, str] = {}
    expected_trigger_id: int | None = None
