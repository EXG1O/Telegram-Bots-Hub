from telegram import Message, Update

from service import Connection
import service

from ...context import Context
from ...storage import Storage, SubscriptionType, UserStorageData
from ..base import BaseConnectionFetcher

from itertools import chain


class SubscriptionMessageKeyboardButtonConnectionFetcher(BaseConnectionFetcher):
    async def fetch(self, update: Update, context: Context) -> list[Connection] | None:
        message: Message | None = update.message
        user_storage: Storage[UserStorageData] | None = context.user_storage

        if not (message and user_storage):
            return None

        message_text: str | None = message.text

        if not (message_text and len(message_text) <= 512):
            return None

        storage_data: UserStorageData = await user_storage.get_data()
        button_ids: set[int] = storage_data.subscriptions[
            SubscriptionType.MESSAGE_KEYBOARD_BUTTON
        ]

        if not button_ids:
            return None

        buttons: list[
            service.MessageKeyboardButton
        ] = await self._bot.service.get_messages_keyboard_buttons(
            ids=button_ids, type=service.MessageKeyboardType.DEFAULT, text=message_text
        )

        async with user_storage.transaction() as storage_data:
            storage_data.subscriptions[SubscriptionType.MESSAGE_KEYBOARD_BUTTON] = set()

        return list(
            chain.from_iterable(button.source_connections for button in buttons)
        )
