from typing import TypedDict


class CreateUserData(TypedDict):
	telegram_id: int
	full_name: str


class CreateDatabaseRecord(TypedDict):
	data: str
