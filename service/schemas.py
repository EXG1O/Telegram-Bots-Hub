from typing import Any, TypedDict


class CreateUserData(TypedDict):
	telegram_id: int
	full_name: str


class CreateDatabaseRecord(TypedDict):
	data: dict[str, Any]
