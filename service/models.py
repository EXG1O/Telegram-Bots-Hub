import msgspec

from .enums import (
    APIRequestMethod,
    BackgroundTaskInterval,
    ConditionPartNextPartOperator,
    ConditionPartOperator,
    ConditionPartType,
    ConnectionSourceObjectType,
    ConnectionTargetObjectType,
    MessageKeyboardButtonStyle,
    MessageKeyboardType,
)

from typing import Any


class ServiceObject(msgspec.Struct):
    pass


class Media(ServiceObject):
    name: str | None
    size: int | None
    url: str | None
    from_url: str | None


class Bot(ServiceObject):
    id: int
    is_private: bool


class Connection(ServiceObject):
    id: int
    source_object_type: ConnectionSourceObjectType
    source_object_id: int
    target_object_type: ConnectionTargetObjectType
    target_object_id: int


class TriggerCommand(ServiceObject):
    command: str
    payload: str | None
    description: str | None


class TriggerMessage(ServiceObject):
    text: str | None


class Trigger(ServiceObject):
    id: int
    command: TriggerCommand | None
    message: TriggerMessage | None
    source_connections: list[Connection]


class MessageSettings(ServiceObject):
    reply_to_user_message: bool
    delete_user_message: bool
    send_as_new_message: bool


class MessageMedia(Media):
    id: int
    position: int


class MessageImage(MessageMedia):
    pass


class MessageDocument(MessageMedia):
    pass


class MessageKeyboardButton(ServiceObject):
    id: int
    row: int
    position: int
    text: str
    url: str | None
    style: MessageKeyboardButtonStyle
    source_connections: list[Connection]


class MessageKeyboard(ServiceObject):
    type: MessageKeyboardType
    buttons: list[MessageKeyboardButton]


class Message(ServiceObject):
    id: int
    text: str | None
    settings: MessageSettings
    images: list[MessageImage]
    documents: list[MessageDocument]
    keyboard: MessageKeyboard | None
    source_connections: list[Connection]


class ConditionPart(ServiceObject):
    id: int
    type: ConditionPartType
    first_value: str
    operator: ConditionPartOperator
    second_value: str
    next_part_operator: ConditionPartNextPartOperator | None


class Condition(ServiceObject):
    id: int
    parts: list[ConditionPart]
    source_connections: list[Connection]


class BackgroundTask(ServiceObject):
    id: int
    interval: BackgroundTaskInterval
    source_connections: list[Connection]


class APIRequest(ServiceObject):
    id: int
    url: str
    method: APIRequestMethod
    headers: dict[str, Any] | None
    body: dict[str, Any] | list[Any] | None
    source_connections: list[Connection]


class DatabaseCreateOperation(ServiceObject):
    data: dict[str, Any] | list[Any]


class DatabaseUpdateOperation(ServiceObject):
    overwrite: bool
    lookup_field_name: str
    lookup_field_value: str
    create_if_not_found: bool
    new_data: dict[str, Any] | list[Any]


class DatabaseOperation(ServiceObject):
    id: int
    create_operation: DatabaseCreateOperation | None
    update_operation: DatabaseUpdateOperation | None
    source_connections: list[Connection]


class InvoiceImage(Media):
    pass


class InvoicePrice(ServiceObject):
    id: int
    label: str
    amount: int


class Invoice(ServiceObject):
    id: int
    title: str
    image: InvoiceImage | None
    description: str
    prices: list[InvoicePrice]
    source_connections: list[Connection]


class TemporaryVariable(ServiceObject):
    id: int
    name: str
    value: str
    source_connections: list[Connection]


class Variable(ServiceObject):
    id: int
    name: str
    value: str


class User(ServiceObject):
    id: int
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    is_bot: bool
    is_premium: bool
    is_allowed: bool
    is_blocked: bool


class DatabaseRecord(ServiceObject):
    id: int
    data: dict[str, Any] | list[Any]
