from enum import StrEnum


class UpdateType(StrEnum):
    MESSAGE = 'message'
    CALLBACK_QUERY = 'callback_query'
    PRE_CHECKOUT_QUERY = 'pre_checkout_query'


class ChatType(StrEnum):
    PRIVATE = 'private'
    GROUP = 'group'
    SUPERGROUP = 'supergroup'
    CHANNEL = 'channel'


class InputMediaType(StrEnum):
    PHOTO = 'photo'
    DOCUMENT = 'document'
    VIDEO = 'video'
    AUDIO = 'audio'


class KeyboardButtonStyle(StrEnum):
    PRIMARY = 'primary'
    SUCCESS = 'success'
    DANGER = 'danger'
