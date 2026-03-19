from telegram.exceptions import (
    BadRequestError,
    ChatMigratedError,
    ConflictError,
    ForbiddenError,
    InvalidTokenError,
    NetworkError,
)
from telegram.utils import prepare_request_data

from aiohttp import ClientSession, DummyCookieJar, hdrs
from aiohttp.typedefs import LooseHeaders
from yarl import URL
import msgspec

from core.msgspec import json_encoder

from .constants import PARSE_MODE
from .enums import UpdateType
from .models import (
    BotCommand,
    InputMedia,
    LabeledPrice,
    Message,
    ReplyParameters,
    TelegramResponse,
    User,
)
from .types import KeyboardMarkup

from http import HTTPStatus
from typing import Any, Final
import asyncio
import logging

logger = logging.getLogger(__name__)


HEADERS: Final[LooseHeaders] = {
    hdrs.USER_AGENT: 'ConstructorTelegramBots (constructor.exg1o.org)',
    hdrs.CONTENT_TYPE: 'application/json',
}

get_me_decoder = msgspec.json.Decoder(TelegramResponse[User])
set_webhook_decoder = msgspec.json.Decoder(TelegramResponse[bool])
delete_webhook_decoder = msgspec.json.Decoder(TelegramResponse[bool])
set_my_commands_decoder = msgspec.json.Decoder(TelegramResponse[bool])
send_invoice_decoder = msgspec.json.Decoder(TelegramResponse[Message])
answer_pre_checkout_query_decoder = msgspec.json.Decoder(TelegramResponse[bool])
send_message_decoder = msgspec.json.Decoder(TelegramResponse[Message])
send_photo_decoder = msgspec.json.Decoder(TelegramResponse[Message])
send_document_decoder = msgspec.json.Decoder(TelegramResponse[Message])
send_media_group_decoder = msgspec.json.Decoder(TelegramResponse[list[Message]])
delete_message_decoder = msgspec.json.Decoder(TelegramResponse[bool])
delete_messages_decoder = msgspec.json.Decoder(TelegramResponse[bool])


class TelegramClient:
    _session: ClientSession | None = None

    def __init__(self, bot_token: str) -> None:
        self.url = URL(f'https://api.telegram.org/bot{bot_token}')

    @classmethod
    def get_session(cls) -> ClientSession:
        if not cls._session:
            cls._session = ClientSession(headers=HEADERS, cookie_jar=DummyCookieJar())
        return cls._session

    @property
    def session(self) -> ClientSession:
        return self.get_session()

    async def _request[T](
        self,
        endpoint: str,
        decoder: msgspec.json.Decoder[TelegramResponse[T]],
        data: dict[str, Any] | None = None,
    ) -> T:
        try:
            async with self.session.post(
                self.url / endpoint,
                data=data and json_encoder.encode(prepare_request_data(data)),
            ) as response:
                body: bytes = await response.read()

            response_status = HTTPStatus(response.status)
            response_data: TelegramResponse[T] = decoder.decode(body)

            if response_status.is_success and response_data.result:
                return response_data.result

            message: str | None = response_data.description

            if not message:
                message = f'{response_status.description} ({response_status})'

            if parameters := response_data.parameters:
                if parameters.migrate_to_chat_id:
                    raise ChatMigratedError(message)  # noqa: TRY301
                elif retry_after := parameters.retry_after:
                    await asyncio.sleep(retry_after)
                    return await self._request(endpoint, decoder, data)

            if response_status in (HTTPStatus.NOT_FOUND, HTTPStatus.UNAUTHORIZED):
                raise InvalidTokenError(message)  # noqa: TRY301
            elif response_status == HTTPStatus.FORBIDDEN:
                raise ForbiddenError(message)  # noqa: TRY301
            elif response_status == HTTPStatus.BAD_REQUEST:
                raise BadRequestError(message)  # noqa: TRY301
            elif response_status == HTTPStatus.CONFLICT:
                raise ConflictError(message)  # noqa: TRY301

            raise NetworkError(message)  # noqa: TRY301
        except Exception as error:
            logger.exception('Failed request to the Telegram Bot API.')
            raise error

    async def get_me(self) -> User:
        return await self._request('getMe', decoder=get_me_decoder)

    async def set_webhook(
        self, url: str, allowed_updates: list[UpdateType], secret_token: str
    ) -> bool:
        return await self._request(
            'setWebhook',
            data={
                'url': url,
                'allowed_updates': allowed_updates,
                'secret_token': secret_token,
            },
            decoder=set_webhook_decoder,
        )

    async def delete_webhook(self) -> bool:
        return await self._request('deleteWebhook', decoder=delete_webhook_decoder)

    async def set_my_commands(self, commands: list[BotCommand]) -> bool:
        return await self._request(
            'setMyCommands',
            data={'commands': commands},
            decoder=set_my_commands_decoder,
        )

    async def send_invoice(
        self,
        chat_id: int,
        title: str,
        description: str,
        prices: list[LabeledPrice],
        photo_url: str | None = None,
        provider_token: str = '',
        payload: str = 'empty',
        currency: str = 'XTR',
        protect_content: bool | None = None,
    ) -> Message:
        return await self._request(
            'sendInvoice',
            data={
                'chat_id': chat_id,
                'title': title,
                'photo_url': photo_url,
                'description': description,
                'provider_token': provider_token,
                'payload': payload,
                'currency': currency,
                'prices': prices,
                'protect_content': protect_content,
            },
            decoder=send_invoice_decoder,
        )

    async def answer_pre_checkout_query(
        self, pre_checkout_query_id: str, ok: bool
    ) -> bool:
        return await self._request(
            'answerPreCheckoutQuery',
            data={'pre_checkout_query_id': pre_checkout_query_id, 'ok': ok},
            decoder=answer_pre_checkout_query_decoder,
        )

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_parameters: ReplyParameters | None = None,
        reply_markup: KeyboardMarkup | None = None,
    ) -> Message:
        return await self._request(
            'sendMessage',
            data={
                'chat_id': chat_id,
                'reply_parameters': reply_parameters,
                'text': text,
                'parse_mode': PARSE_MODE,
                'reply_markup': reply_markup,
            },
            decoder=send_message_decoder,
        )

    async def send_photo(
        self,
        chat_id: int,
        photo: str,
        reply_parameters: ReplyParameters | None = None,
        caption: str | None = None,
        reply_markup: KeyboardMarkup | None = None,
    ) -> Message:
        return await self._request(
            'sendPhoto',
            data={
                'chat_id': chat_id,
                'reply_parameters': reply_parameters,
                'photo': photo,
                'caption': caption,
                'parse_mode': PARSE_MODE,
                'reply_markup': reply_markup,
            },
            decoder=send_photo_decoder,
        )

    async def send_document(
        self,
        chat_id: int,
        document: str,
        reply_parameters: ReplyParameters | None = None,
        caption: str | None = None,
        reply_markup: KeyboardMarkup | None = None,
    ) -> Message:
        return await self._request(
            'sendDocument',
            data={
                'chat_id': chat_id,
                'reply_parameters': reply_parameters,
                'document': document,
                'caption': caption,
                'parse_mode': PARSE_MODE,
                'reply_markup': reply_markup,
            },
            decoder=send_document_decoder,
        )

    async def send_media_group(
        self,
        chat_id: int,
        media: list[InputMedia],
        reply_parameters: ReplyParameters | None = None,
    ) -> list[Message]:
        return await self._request(
            'sendMediaGroup',
            data={
                'chat_id': chat_id,
                'reply_parameters': reply_parameters,
                'media': media,
            },
            decoder=send_media_group_decoder,
        )

    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        return await self._request(
            'deleteMessage',
            data={'chat_id': chat_id, 'message_id': message_id},
            decoder=delete_messages_decoder,
        )

    async def delete_messages(self, chat_id: int, message_ids: list[int]) -> bool:
        return await self._request(
            'deleteMessages',
            data={'chat_id': chat_id, 'message_ids': message_ids},
            decoder=delete_messages_decoder,
        )
