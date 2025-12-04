from .base_models import MessageMedia
from .enums import (
    APIRequestMethod,
    BackgroundTaskInterval,
    ConditionPartNextPartOperator,
    ConditionPartOperator,
    ConditionPartType,
    ConnectionSourceObjectType,
    ConnectionTargetObjectType,
    MessageKeyboardType,
)

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Bot:
    id: int
    is_private: bool


@dataclass(frozen=True)
class Connection:
    id: int
    source_object_type: ConnectionSourceObjectType
    source_object_id: int
    target_object_type: ConnectionTargetObjectType
    target_object_id: int


@dataclass(frozen=True)
class TriggerCommand:
    command: str
    payload: str | None
    description: str | None


@dataclass(frozen=True)
class TriggerMessage:
    text: str | None


@dataclass(frozen=True)
class Trigger:
    id: int
    command: TriggerCommand | None
    message: TriggerMessage | None
    source_connections: list[Connection]


@dataclass(frozen=True)
class MessageSettings:
    reply_to_user_message: bool
    delete_user_message: bool
    send_as_new_message: bool


@dataclass(frozen=True)
class MessageImage(MessageMedia):
    pass


@dataclass(frozen=True)
class MessageDocument(MessageMedia):
    pass


@dataclass(frozen=True)
class MessageKeyboardButton:
    id: int
    row: int
    position: int
    text: str
    url: str | None
    source_connections: list[Connection]


@dataclass(frozen=True)
class MessageKeyboard:
    type: MessageKeyboardType
    buttons: list[MessageKeyboardButton]


@dataclass(frozen=True)
class Message:
    id: int
    text: str
    settings: MessageSettings
    images: list[MessageImage]
    documents: list[MessageDocument]
    keyboard: MessageKeyboard | None
    source_connections: list[Connection]


@dataclass(frozen=True)
class ConditionPart:
    id: int
    type: ConditionPartType
    first_value: str
    operator: ConditionPartOperator
    second_value: str
    next_part_operator: ConditionPartNextPartOperator | None


@dataclass(frozen=True)
class Condition:
    id: int
    parts: list[ConditionPart]
    source_connections: list[Connection]


@dataclass(frozen=True)
class BackgroundTask:
    id: int
    interval: BackgroundTaskInterval
    source_connections: list[Connection]


@dataclass(frozen=True)
class APIRequest:
    id: int
    url: str
    method: APIRequestMethod
    headers: dict[str, Any] | None
    body: dict[str, Any] | list[Any] | None
    source_connections: list[Connection]


@dataclass(frozen=True)
class DatabaseCreateOperation:
    data: dict[str, Any] | list[Any]


@dataclass(frozen=True)
class DatabaseUpdateOperation:
    overwrite: bool
    lookup_field_name: str
    lookup_field_value: str
    create_if_not_found: bool
    new_data: dict[str, Any] | list[Any]


@dataclass(frozen=True)
class DatabaseOperation:
    id: int
    create_operation: DatabaseCreateOperation | None
    update_operation: DatabaseUpdateOperation | None
    source_connections: list[Connection]


@dataclass(frozen=True)
class Variable:
    id: int
    name: str
    value: str


@dataclass(frozen=True)
class User:
    id: int
    telegram_id: int
    full_name: str
    is_allowed: bool
    is_blocked: bool


@dataclass(frozen=True)
class DatabaseRecord:
    id: int
    data: dict[str, Any] | list[Any]
