from dataclasses import dataclass
from typing import Literal, NotRequired, TypedDict


@dataclass
class ServiceBot:
	id: int
	is_private: bool
	is_enabled: bool
	is_loading: bool


class UpdateServiceBotData(TypedDict):
	is_enabled: NotRequired[bool]
	is_loading: NotRequired[bool]


@dataclass
class ServiceBotCommandSettings:
	is_reply_to_user_message: bool
	is_delete_user_message: bool
	is_send_as_new_message: bool


@dataclass
class ServiceBotCommandCommand:
	text: str
	description: str | None


@dataclass
class ServiceBotCommandImage:
	name: str
	url: str


@dataclass
class ServiceBotCommandFile:
	name: str
	url: str


@dataclass
class ServiceBotCommandMessageText:
	text: str


@dataclass
class ServiceBotCommandKeyboardButton:
	id: int
	row: int | None
	text: str
	url: str | None


@dataclass
class ServiceBotCommandKeyboard:
	type: Literal['default', 'inline', 'payment']
	buttons: list[ServiceBotCommandKeyboardButton]


@dataclass
class ServiceBotCommandAPIRequest:
	url: str
	method: Literal['get', 'post', 'put', 'patch', 'delete']
	headers: str | None
	body: str | None


@dataclass
class ServiceBotCommandDatabaseRecord:
	data: str


@dataclass
class ServiceBotCommand:
	id: int
	name: str
	settings: ServiceBotCommandSettings
	command: ServiceBotCommandCommand | None
	images: list[ServiceBotCommandImage]
	files: list[ServiceBotCommandFile]
	message_text: ServiceBotCommandMessageText
	keyboard: ServiceBotCommandKeyboard | None
	api_request: ServiceBotCommandAPIRequest | None
	database_record: ServiceBotCommandDatabaseRecord | None


@dataclass
class ServiceBotVariable:
	id: int
	name: str
	value: str


@dataclass
class ServiceBotUser:
	id: int
	telegram_id: int
	full_name: str
	is_allowed: bool
	is_blocked: bool
