from telegram import (
    Chat,
    InputMediaDocument,
    InputMediaPhoto,
    Message,
    Update,
    User,
)
from telegram._utils.types import ReplyMarkup
from telegram.constants import MediaGroupLimit

from service.models import Connection
from service.models import Message as SMessage

from ...storage import EventStorage
from ...utils import process_html_text, replace_text_variables
from ...variables import Variables
from ..base import BaseHandler
from .data import Media, MediaType, MediaValue
from .utils import build_keyboard, prepare_media

from collections.abc import Awaitable, Callable
from typing import Any, cast
import asyncio


class MessageHandler(BaseHandler[SMessage]):
    async def _send_media_group(
        self,
        chat_id: int,
        media: Media,
        message_text: str,
        reply_to_message_id: int | None = None,
        keyboard: ReplyMarkup | None = None,
    ) -> list[Message]:
        kwargs: dict[str, Any] = {
            'chat_id': chat_id,
            'reply_to_message_id': reply_to_message_id,
        }

        if not any(media.values()):
            return [
                await self.bot.telegram.send_message(
                    text=message_text, reply_markup=keyboard, **kwargs
                )
            ]

        new_bot_messages: list[Message] = []
        processed_types: set[MediaType] = set()
        text_attached: bool = False

        for type, files in media.items():
            type = cast(MediaType, type)
            files = cast(MediaValue, files)

            if not files:
                continue

            processed_types.add(type)

            if len(files) < MediaGroupLimit.MIN_MEDIA_LENGTH:
                should_attach_text: bool = not any(
                    len(media[other_type]) > 0  # type: ignore [literal-required]
                    for other_type in media
                    if other_type not in processed_types
                )

                send_file: Callable[..., Awaitable[Message]] = getattr(
                    self.bot.telegram, f'send_{type}'
                )

                custom_kwargs: dict[str, Any] = kwargs.copy()
                custom_kwargs[type] = files[0].media

                if should_attach_text and not text_attached:
                    custom_kwargs['caption'] = message_text
                    custom_kwargs['reply_markup'] = keyboard
                    text_attached = True

                new_bot_messages.append(await send_file(**custom_kwargs))
                continue

            for start_index in range(0, len(files), MediaGroupLimit.MAX_MEDIA_LENGTH):
                new_bot_messages.extend(
                    await self.bot.telegram.send_media_group(
                        media=files[
                            start_index : start_index + MediaGroupLimit.MAX_MEDIA_LENGTH
                        ],
                        **kwargs,
                    )
                )

        if not text_attached:
            new_bot_messages.append(
                await self.bot.telegram.send_message(
                    text=message_text, reply_markup=keyboard, **kwargs
                )
            )

        return new_bot_messages

    async def handle(
        self,
        update: Update,
        message: SMessage,
        event_storage: EventStorage,
        variables: Variables,
    ) -> list[Connection] | None:
        chat: Chat | None = update.effective_chat
        user: User | None = update.effective_user

        if not event_storage.chat or not chat or not user:
            return None

        if not message.settings.send_as_new_message:
            last_bot_message_ids: list[int] | None = await event_storage.chat.pop(
                'last_bot_message_ids'
            )

            if last_bot_message_ids:
                await self.bot.telegram.delete_messages(chat.id, last_bot_message_ids)

        event_message: Message | None = update.effective_message
        event_message_id: int | None = (
            event_message.message_id if event_message else None
        )
        photos, documents, message_text, keyboard = await asyncio.gather(
            prepare_media(InputMediaPhoto, message.images),
            prepare_media(InputMediaDocument, message.documents),
            replace_text_variables(process_html_text(message.text), variables),
            build_keyboard(message.keyboard)
            if message.keyboard
            else asyncio.sleep(0, result=None),
        )

        last_bot_messages: list[Message] = await self._send_media_group(
            chat_id=chat.id,
            reply_to_message_id=event_message_id
            if message.settings.reply_to_user_message
            else None,
            media=Media(photo=photos, document=documents, video=[], audio=[]),
            message_text=message_text,
            keyboard=keyboard,
        )
        await event_storage.chat.set(
            'last_bot_message_ids',
            [last_bot_message.id for last_bot_message in last_bot_messages],
        )

        if (
            event_message_id
            and not user.is_bot
            and message.settings.delete_user_message
        ):
            await self.bot.telegram.delete_message(chat.id, event_message_id)

        return message.source_connections
