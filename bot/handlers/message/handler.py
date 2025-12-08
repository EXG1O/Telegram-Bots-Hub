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
from service.models import Message as ServiceMessage

from ...storage import EventStorage, Storage
from ...utils import process_html_text, replace_text_variables
from ...variables import Variables
from ..base import BaseHandler
from .data import Media, MediaType, MediaValue
from .utils import build_keyboard, prepare_media

from collections.abc import Awaitable, Callable
from typing import Any, cast
import asyncio


class MessageHandler(BaseHandler[ServiceMessage]):
    async def _delete_last_bot_messages(
        self, chat: Chat, chat_storage: Storage
    ) -> None:
        last_bot_message_ids: list[int] | None = await chat_storage.pop(
            'last_bot_message_ids'
        )

        if not last_bot_message_ids:
            return

        await self.bot.telegram.delete_messages(chat.id, last_bot_message_ids)

    async def _send_media_group(
        self,
        chat_id: int,
        media: Media,
        text: str | None = None,
        keyboard: ReplyMarkup | None = None,
        reply_to_message_id: int | None = None,
    ) -> list[Message]:
        kwargs: dict[str, Any] = {
            'chat_id': chat_id,
            'reply_to_message_id': reply_to_message_id,
        }

        new_bot_messages: list[Message] = []
        processed_types: set[MediaType] = set()
        extras_attached: bool = False

        for type, files in media.items():
            type = cast(MediaType, type)
            files = cast(MediaValue, files)

            if not files:
                continue

            processed_types.add(type)

            if len(files) < MediaGroupLimit.MIN_MEDIA_LENGTH:
                should_attach_extras: bool = bool(text) and not any(
                    len(media[other_type]) > 0  # type: ignore [literal-required]
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

        if text and not extras_attached:
            new_bot_messages.append(
                await self.bot.telegram.send_message(
                    text=text, reply_markup=keyboard, **kwargs
                )
            )

        return new_bot_messages

    async def _process_message(
        self,
        chat: Chat,
        event_message_id: int | None,
        message: ServiceMessage,
        chat_storage: Storage,
        variables: Variables,
    ) -> None:
        reply_to_message_id: int | None = (
            event_message_id if message.settings.reply_to_user_message else None
        )
        photos, documents, text, keyboard = await asyncio.gather(
            prepare_media(InputMediaPhoto, message.images),
            prepare_media(InputMediaDocument, message.documents),
            replace_text_variables(process_html_text(message.text), variables)
            if message.text
            else asyncio.sleep(0),
            build_keyboard(message.keyboard) if message.keyboard else asyncio.sleep(0),
        )
        media = Media(photo=photos, document=documents, video=[], audio=[])

        last_bot_messages: list[Message] = []

        if text and not any(media.values()):
            last_bot_messages.append(
                await self.bot.telegram.send_message(
                    chat.id,
                    reply_to_message_id=reply_to_message_id,
                    text=text,
                    reply_markup=keyboard,
                )
            )
        else:
            last_bot_messages.extend(
                await self._send_media_group(
                    chat.id,
                    reply_to_message_id=reply_to_message_id,
                    media=media,
                    text=text,
                    keyboard=keyboard,
                )
            )

        await chat_storage.set(
            'last_bot_message_ids',
            [last_bot_message.id for last_bot_message in last_bot_messages],
        )

    async def handle(
        self,
        update: Update,
        message: ServiceMessage,
        event_storage: EventStorage,
        variables: Variables,
    ) -> list[Connection] | None:
        chat: Chat | None = update.effective_chat
        user: User | None = update.effective_user
        chat_storage: Storage | None = event_storage.chat

        if not chat or not user or not chat_storage:
            return None

        event_message: Message | None = update.effective_message
        event_message_id: int | None = (
            event_message.message_id if event_message else None
        )

        tasks: list[Awaitable[Any]] = [
            self._process_message(
                chat, event_message_id, message, chat_storage, variables
            )
        ]

        if not message.settings.send_as_new_message:
            tasks.append(self._delete_last_bot_messages(chat, chat_storage))

        await asyncio.gather(*tasks)

        if (
            message.settings.delete_user_message
            and event_message_id
            and not user.is_bot
        ):
            await self.bot.telegram.delete_message(chat.id, event_message_id)

        return message.source_connections
