from .base_models import APIRequest, CommandMedia
from .enums import (
    BackgroundTaskInterval,
    CommandKeyboardType,
    ConditionPartNextPartOperator,
    ConditionPartOperator,
    ConditionPartType,
    ConnectionSourceObjectType,
    ConnectionTargetObjectType,
)

from dataclasses import dataclass
from typing import Any


@dataclass
class Bot:
    id: int
    is_private: bool


@dataclass
class Connection:
    id: int
    source_object_type: ConnectionSourceObjectType
    source_object_id: int
    target_object_type: ConnectionTargetObjectType
    target_object_id: int


@dataclass
class CommandTrigger:
    id: int
    command_id: int
    text: str
    description: str | None


@dataclass
class CommandSettings:
    is_reply_to_user_message: bool
    is_delete_user_message: bool
    is_send_as_new_message: bool


@dataclass
class CommandImage(CommandMedia):
    pass


@dataclass
class CommandDocument(CommandMedia):
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
    source_connections: list[Connection]


@dataclass
class CommandKeyboard:
    type: CommandKeyboardType
    buttons: list[CommandKeyboardButton]


@dataclass
class CommandAPIRequest(APIRequest):
    pass


@dataclass
class CommandDatabaseRecord:
    data: dict[str, Any]


@dataclass
class Command:
    id: int
    name: str
    settings: CommandSettings
    images: list[CommandImage]
    documents: list[CommandDocument]
    message: CommandMessage
    keyboard: CommandKeyboard | None
    api_request: CommandAPIRequest | None
    database_record: CommandDatabaseRecord | None
    target_connections: list[Connection]


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
    source_connections: list[Connection]
    target_connections: list[Connection]


@dataclass
class BackgroundTaskAPIRequest(APIRequest):
    pass


@dataclass
class BackgroundTask:
    id: int
    name: str
    interval: BackgroundTaskInterval
    api_request: BackgroundTaskAPIRequest | None
    source_connections: list[Connection]


@dataclass
class Variable:
    id: int
    name: str
    value: str


@dataclass
class User:
    id: int
    telegram_id: int
    full_name: str
    is_allowed: bool
    is_blocked: bool


@dataclass
class DatabaseRecord:
    id: int
    data: dict[str, Any]
