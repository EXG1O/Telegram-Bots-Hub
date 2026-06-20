from .enums import ChatType

from typing import Any, TypedDict


class CreateChat(TypedDict):
    telegram_id: int
    type: ChatType
    title: str | None
    username: str | None
    first_name: str | None
    last_name: str | None
    is_forum: bool
    is_direct_messages: bool


class BindUserToChat(TypedDict, total=False):
    id: int
    telegram_id: int


class CreateUser(TypedDict):
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    is_bot: bool
    is_premium: bool


class CreateDatabaseRecord(TypedDict):
    data: dict[str, Any] | list[Any]


class UpdateDatabaseRecords(TypedDict):
    data: dict[str, Any] | list[Any]


class UpdateDatabaseRecord(TypedDict):
    data: dict[str, Any] | list[Any]
