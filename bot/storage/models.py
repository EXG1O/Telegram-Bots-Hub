import msgspec

from datetime import datetime


class BotStorageData(msgspec.Struct):
    completed_background_tasks: dict[int, datetime] = {}


class ChatStorageData(msgspec.Struct):
    last_bot_message_ids: list[int] = []


class UserStorageData(msgspec.Struct):
    temporary_variables: dict[str, str] = {}
    expected_trigger_id: int | None = None
