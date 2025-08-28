from typing import Any, TypedDict


class CreateUser(TypedDict):
    telegram_id: int
    full_name: str


class CreateDatabaseRecord(TypedDict):
    data: dict[str, Any] | list[Any]


class UpdateDatabaseRecords(TypedDict):
    data: dict[str, Any] | list[Any]


class UpdateDatabaseRecord(TypedDict):
    data: dict[str, Any] | list[Any]
