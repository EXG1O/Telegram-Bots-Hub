from .base_models import CommandMedia
from .enums import (
    APIRequestMethod,
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
class TriggerCommand:
    command: str
    payload: str | None
    description: str | None


@dataclass
class TriggerMessage:
    text: str


@dataclass
class Trigger:
    id: int
    command: TriggerCommand | None
    message: TriggerMessage | None
    source_connections: list[Connection]


@dataclass
class CommandSettings:
    reply_to_user_message: bool
    delete_user_message: bool
    send_as_new_message: bool


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
class Command:
    id: int
    settings: CommandSettings
    images: list[CommandImage]
    documents: list[CommandDocument]
    message: CommandMessage
    keyboard: CommandKeyboard | None


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
    parts: list[ConditionPart]
    source_connections: list[Connection]


@dataclass
class BackgroundTask:
    id: int
    interval: BackgroundTaskInterval
    source_connections: list[Connection]


@dataclass
class APIRequest:
    id: int
    url: str
    method: APIRequestMethod
    headers: dict[str, Any] | None
    body: dict[str, Any] | list[Any] | None
    source_connections: list[Connection]


@dataclass
class DatabaseCreateOperation:
    data: dict[str, Any] | list[Any]


@dataclass
class DatabaseUpdateOperation:
    overwrite: bool
    lookup_field_name: str
    lookup_field_value: str
    create_if_not_found: bool
    new_data: dict[str, Any] | list[Any]


@dataclass
class DatabaseOperation:
    id: int
    create_operation: DatabaseCreateOperation | None
    update_operation: DatabaseUpdateOperation | None
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
    data: dict[str, Any] | list[Any]
