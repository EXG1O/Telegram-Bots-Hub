from telegram import CallbackQuery, Update

from service import Connection
import service

from ..context import Context
from .base import BaseConnectionFetcher


class MessageKeyboardButtonConnectionFetcher(BaseConnectionFetcher):
    async def fetch(self, update: Update, context: Context) -> list[Connection] | None:
        callback_query: CallbackQuery | None = update.callback_query

        if not callback_query:
            return None

        callback_data: str | None = callback_query.data

        if not (callback_data and callback_data.isdigit()):
            return None

        button: service.MessageKeyboardButton = (
            await self._bot.service.get_messages_keyboard_button(id=int(callback_data))
        )
        return button.source_connections
