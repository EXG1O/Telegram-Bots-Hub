from typing import Any, TypedDict


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
