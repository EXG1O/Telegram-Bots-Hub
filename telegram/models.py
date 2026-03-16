from telegram.utils import get_subject_full_name, get_subject_link, get_subject_name

import msgspec

from .constants import PARSE_MODE
from .enums import ChatType, InputMediaType, KeyboardButtonStyle


class TelegramObject(msgspec.Struct):
    pass


class BotCommand(TelegramObject):
    command: str
    description: str


class KeyboardButton(TelegramObject):
    text: str
    style: KeyboardButtonStyle | None = None


class ReplyKeyboardMarkup(TelegramObject):
    keyboard: list[list[KeyboardButton]]
    resize_keyboard: bool


class InlineKeyboardButton(TelegramObject):
    text: str
    style: KeyboardButtonStyle | None = None
    url: str | None = None
    callback_data: str | None = None


class InlineKeyboardMarkup(TelegramObject):
    inline_keyboard: list[list[InlineKeyboardButton]]


class ReplyParameters(TelegramObject):
    message_id: int
    chat_id: int | None = None


class InputMedia(TelegramObject):
    type: InputMediaType
    media: str
    caption: str | None = None
    parse_mode: str = PARSE_MODE


class LabeledPrice(TelegramObject):
    label: str
    amount: int


class Chat(TelegramObject):
    id: int
    type: ChatType
    title: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    @property
    def full_name(self) -> str | None:
        return get_subject_full_name(self)

    @property
    def link(self) -> str | None:
        return get_subject_link(self)

    @property
    def effective_name(self) -> str | None:
        if self.title is not None:
            return self.title
        if self.full_name is not None:
            return self.full_name
        return None


class User(TelegramObject):
    id: int
    is_bot: bool
    first_name: str
    username: str | None = None
    last_name: str | None = None
    is_premium: bool = False
    language_code: str | None = None

    @property
    def name(self) -> str:
        return get_subject_name(self)

    @property
    def full_name(self) -> str:
        return get_subject_full_name(self)

    @property
    def link(self) -> str | None:
        return get_subject_link(self)


class Message(TelegramObject):
    message_id: int
    chat: Chat
    date: int
    user: User | None = msgspec.field(name='from', default=None)
    text: str | None = None

    @property
    def link(self) -> str | None:
        if self.chat.type in (ChatType.PRIVATE, ChatType.GROUP):
            return None

        to_link: str = self.chat.username or f'c/{str(self.chat.id)[4:]}'
        return f'https://t.me/{to_link}/{self.message_id}'


class CallbackQuery(TelegramObject):
    id: str
    data: str
    user: User | None = msgspec.field(name='from', default=None)
    message: Message | None = None


class PreCheckoutQuery(TelegramObject):
    id: str
    user: User = msgspec.field(name='from')


class Update(TelegramObject):
    update_id: int
    message: Message | None = None
    callback_query: CallbackQuery | None = None
    pre_checkout_query: PreCheckoutQuery | None = None

    _effective_chat: Chat | None = None
    _effective_user: User | None = None
    _effective_message: Message | None = None

    @property
    def effective_chat(self) -> Chat | None:
        if self._effective_chat:
            return self._effective_chat

        result: Chat | None = None

        if self.message:
            result = self.message.chat
        elif self.callback_query and self.callback_query.message:
            result = self.callback_query.message.chat

        self._effective_chat = result
        return result

    @property
    def effective_user(self) -> User | None:
        if self._effective_user:
            return self._effective_user

        result: User | None = None

        if self.message:
            result = self.message.user
        elif self.callback_query:
            result = self.callback_query.user
        elif self.pre_checkout_query:
            result = self.pre_checkout_query.user

        self._effective_user = result
        return result

    @property
    def effective_message(self) -> Message | None:
        if self._effective_message:
            return self._effective_message

        result: Message | None = None

        if self.message:
            result = self.message
        elif self.callback_query and self.callback_query.message:
            result = self.callback_query.message

        self._effective_message = result
        return result


class ResponseParameters(msgspec.Struct):
    migrate_to_chat_id: int | None = None
    retry_after: int | None = None


class TelegramResponse[T](msgspec.Struct):
    ok: bool
    result: T | None = None
    parameters: ResponseParameters | None = None
    description: str | None = None
