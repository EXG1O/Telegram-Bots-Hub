from .base_data import APIRequest, CommandMedia
from .enums import (
	BackgroundTaskInterval,
	CommandKeyboardType,
	ConditionPartNextPartOperator,
	ConditionPartOperator,
	ConditionPartType,
)

from dataclasses import dataclass


@dataclass
class Bot:
	id: int
	api_token: str
	is_private: bool
	must_be_enabled: bool
	is_enabled: bool


@dataclass
class Connection:
	pass


@dataclass
class CommandSettings:
	is_reply_to_user_message: bool
	is_delete_user_message: bool
	is_send_as_new_message: bool


@dataclass
class CommandTrigger:
	text: str
	description: str | None


@dataclass
class CommandImage(CommandMedia):
	pass


@dataclass
class CommandFile(CommandMedia):
	pass


@dataclass
class CommandMessage:
	text: str


@dataclass
class CommandKeyboardButton:
	id: int
	row: int
	position: int
	text: str
	url: str | None


@dataclass
class CommandKeyboard:
	type: CommandKeyboardType
	buttons: list[CommandKeyboardButton]


@dataclass
class CommandAPIRequest(APIRequest):
	pass


@dataclass
class CommandDatabaseRecord:
	data: str


@dataclass
class Command:
	id: int
	name: str
	settings: CommandSettings
	trigger: CommandTrigger | None
	images: list[CommandImage]
	files: list[CommandFile]
	message: CommandMessage
	keyboard: CommandKeyboard | None
	api_request: CommandAPIRequest | None
	database_record: CommandDatabaseRecord | None


@dataclass
class ConditionPart:
	id: int
	type: ConditionPartType
	first_value: str
	operator: ConditionPartOperator
	second_value: str
	next_part_operator: ConditionPartNextPartOperator | None


@dataclass
class Condition:
	id: int
	name: str
	parts: list[ConditionPart]


@dataclass
class BackgroundTaskAPIRequest(APIRequest):
	pass


@dataclass
class BackgroundTask:
	id: int
	name: str
	interval: BackgroundTaskInterval
	api_request: BackgroundTaskAPIRequest


@dataclass
class Variable:
	id: int
	name: str
	value: str
	description: str


@dataclass
class User:
	id: int
	telegram_id: int
	full_name: str
	is_allowed: bool
	is_blocked: bool
