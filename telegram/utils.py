import msgspec

from typing import TYPE_CHECKING, Any, overload

if TYPE_CHECKING:
    from .models import Chat, User
else:
    Chat = Any
    User = Any


def prepare_request_data(obj: Any) -> Any:
    if isinstance(obj, msgspec.Struct):
        return prepare_request_data(msgspec.to_builtins(obj))
    elif isinstance(obj, dict):
        return {
            key: prepare_request_data(value)
            for key, value in obj.items()
            if value is not None
        }
    elif isinstance(obj, list):
        return [prepare_request_data(item) for item in obj]
    return obj


@overload
def get_subject_name(subject: Chat) -> str | None: ...
@overload
def get_subject_name(subject: User) -> str: ...
def get_subject_name(subject: Chat | User) -> str | None:
    if subject.username:
        return f'@{subject.username}'
    return get_subject_full_name(subject)


@overload
def get_subject_full_name(subject: Chat) -> str | None: ...
@overload
def get_subject_full_name(subject: User) -> str: ...
def get_subject_full_name(subject: Chat | User) -> str | None:
    if not subject.first_name:
        return None
    if subject.last_name:
        return f'{subject.first_name} {subject.last_name}'
    return subject.first_name


def get_subject_link(subject: Chat | User) -> str | None:
    if subject.username:
        return f'https://t.me/{subject.username}'
    return None
