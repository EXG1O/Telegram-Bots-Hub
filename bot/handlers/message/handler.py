from telegram.constants import MediaGroupLimit
from telegram.enums import InputMediaType
from telegram.models import Chat, Message, ReplyParameters, Update
from telegram.types import KeyboardMarkup

from service.models import Connection
from service.models import Message as ServiceMessage

from ...context import HandlerContext
from ...storage import Storage
from ...storage.models import ChatStorageData
from ...utils.html import process_html_text
from ...utils.variables import replace_text_variables
from ...variables import Variables
from ..base import BaseHandler
from .types import Media
from .utils import build_keyboard, prepare_media

from collections.abc import Awaitable, Callable
from typing import Any
import asyncio
import html


class MessageHandler(BaseHandler[ServiceMessage]):
    async def _send_media_group(
        self,
        chat_id: int,
        media: Media,
        text: str | None = None,
        reply_parameters: ReplyParameters | None = None,
        keyboard: KeyboardMarkup | None = None,
    ) -> list[Message]:
        kwargs: dict[str, Any] = {
            'chat_id': chat_id,
            'reply_parameters': reply_parameters,
        }

        bot_messages: list[Message] = []
        processed_types: set[InputMediaType] = set()
        extras_attached: bool = False

        for type, files in media.items():
            if not files:
                continue

            processed_types.add(type)

            if len(files) < MediaGroupLimit.MIN_MEDIA_LENGTH:
                should_attach_extras: bool = bool(text) and not any(
                    len(media[other_type]) > 0
                    for other_type in media
                    if other_type not in processed_types
                )

                custom_kwargs: dict[str, Any] = kwargs.copy()
                custom_kwargs[type] = files[0].media

                if should_attach_extras and not extras_attached:
                    custom_kwargs['caption'] = text
                    custom_kwargs['reply_markup'] = keyboard
                    extras_attached = True

                send_file: Callable[..., Awaitable[Message]] = getattr(
                    self.bot.telegram, f'send_{type}'
                )
                bot_messages.append(await send_file(**custom_kwargs))
                continue

            for start_index in range(0, len(files), MediaGroupLimit.MAX_MEDIA_LENGTH):
                bot_messages.extend(
                    await self.bot.telegram.send_media_group(
                        media=files[
                            start_index : start_index + MediaGroupLimit.MAX_MEDIA_LENGTH
                        ],
                        **kwargs,
                    )
                )

        if text and not extras_attached:
            bot_messages.append(
                await self.bot.telegram.send_message(
                    text=text, reply_markup=keyboard, **kwargs
                )
            )

        return bot_messages

    async def _process_message(
        self,
        chat: Chat,
        reply_to_event_message_id: int | None,
        message: ServiceMessage,
        variables: Variables,
    ) -> list[Message]:
        reply_parameters: ReplyParameters | None = (
            ReplyParameters(message_id=reply_to_event_message_id)
            if message.settings.reply_to_user_message and reply_to_event_message_id
            else None
        )
        media: Media = {
            InputMediaType.PHOTO: prepare_media(
                type=InputMediaType.PHOTO, message_media=message.images
            ),
            InputMediaType.DOCUMENT: prepare_media(
                type=InputMediaType.DOCUMENT, message_media=message.documents
            ),
        }
        text: str | None = (
            process_html_text(
                await replace_text_variables(
                    html.unescape(message.text).replace('\u00a0', ' '), variables
                )
            )
            if message.text
            else None
        )
        keyboard: KeyboardMarkup | None = (
            build_keyboard(message.keyboard) if message.keyboard else None
        )

        bot_messages: list[Message] = []

        if text and not any(media.values()):
            bot_messages.append(
                await self.bot.telegram.send_message(
                    chat_id=chat.id,
                    reply_parameters=reply_parameters,
                    text=text,
                    reply_markup=keyboard,
                )
            )
        else:
            bot_messages.extend(
                await self._send_media_group(
                    chat_id=chat.id,
                    reply_parameters=reply_parameters,
                    media=media,
                    text=text,
                    keyboard=keyboard,
                )
            )

        return bot_messages

    async def handle(
        self, update: Update, message: ServiceMessage, context: HandlerContext
    ) -> list[Connection] | None:
        chat: Chat | None = update.effective_chat
        chat_storage: Storage[ChatStorageData] | None = context.chat_storage

        if not (chat and chat_storage):
            return None

        storage_data: ChatStorageData = await chat_storage.get_data()
        old_last_bot_message_ids: list[int] = storage_data.last_bot_message_ids

        reply_to_event_message_id: int | None = (
            event_message.message_id
            if (
                (event_message := update.effective_message)
                and (event_message_user := event_message and event_message.user)
                and event_message_user.id != self.bot.telegram_id
            )
            else None
        )

        bot_messages: list[Message] = await self._process_message(
            chat, reply_to_event_message_id, message, context.variables
        )

        async with chat_storage.transaction() as storage_data:
            storage_data.last_bot_message_ids = [
                bot_message.message_id for bot_message in bot_messages
            ]

        if not message.settings.send_as_new_message and old_last_bot_message_ids:
            asyncio.create_task(
                self.bot.telegram.delete_messages(chat.id, old_last_bot_message_ids)
            )
        if message.settings.delete_user_message and reply_to_event_message_id:
            asyncio.create_task(
                self.bot.telegram.delete_message(chat.id, reply_to_event_message_id)
            )

        return message.source_connections
