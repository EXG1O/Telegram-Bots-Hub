from telegram import CallbackQuery, Message, Update
from telegram.ext import ContextTypes

from service.models import CommandKeyboardButton, Connection, Trigger

from ..utils import replace_text_variables
from ..variables import Variables
from .connection import ConnectionHandler

from collections.abc import Awaitable, Callable, Sequence
from itertools import chain
from typing import TYPE_CHECKING, Any
import asyncio

if TYPE_CHECKING:
    from ..bot import Bot
else:
    Bot = Any


class UpdateHandler:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.connection_handler = ConnectionHandler(self.bot)
        self.connection_fetchers: Sequence[
            Callable[[Update, Variables], Awaitable[list[Connection]]]
        ] = [
            self._get_trigger_connections,
            self._get_command_keyboard_button_connections,
        ]

    async def _get_command_triggers(self, message_text: str) -> list[Trigger]:
        if not (message_text.startswith('/') and len(message_text) > 1):
            return []

        command, _, payload = message_text.removeprefix('/').partition(' ')

        return await self.bot.service_api.get_triggers(
            command=command,
            command_payload=payload or None,
            has_command_payload=bool(payload),
        )

    async def _get_message_triggers(
        self, message_text: str, variables: Variables
    ) -> list[Trigger]:
        triggers: list[Trigger] = await self.bot.service_api.get_triggers(
            has_message=True
        )
        triggers_message_text: list[str] = await asyncio.gather(
            *[
                replace_text_variables(trigger.message.text, variables)
                for trigger in triggers
                if trigger.message
            ]
        )
        return [
            trigger
            for trigger, trigger_message_text in zip(
                triggers, triggers_message_text, strict=False
            )
            if message_text == trigger_message_text
        ]

    async def _get_trigger_connections(
        self, update: Update, variables: Variables
    ) -> list[Connection]:
        message: Message | None = update.effective_message

        if not (message and message.text):
            return []

        return list(
            chain.from_iterable(
                trigger.source_connections
                for trigger in chain.from_iterable(
                    await asyncio.gather(
                        self._get_command_triggers(message.text),
                        self._get_message_triggers(message.text, variables),
                    )
                )
            )
        )

    async def _get_command_keyboard_button_connections(
        self, update: Update, variables: Variables
    ) -> list[Connection]:
        message: Message | None = update.effective_message
        callback_query: CallbackQuery | None = update.callback_query

        buttons: list[CommandKeyboardButton] = []

        if callback_query and callback_query.data and callback_query.data.isdigit():
            buttons = await self.bot.service_api.get_commands_keyboard_buttons(
                id=int(callback_query.data)
            )
        elif message and message.text:
            buttons = await self.bot.service_api.get_commands_keyboard_buttons(
                text=message.text
            )

        return list(
            chain.from_iterable(button.source_connections for button in buttons)
        )

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        variables = Variables(self.bot, update.effective_user, update.effective_message)
        await self.connection_handler.handle_many(
            update,
            list(
                chain.from_iterable(
                    await asyncio.gather(
                        *[
                            fetcher(update, variables)
                            for fetcher in self.connection_fetchers
                        ]
                    )
                )
            ),
            variables,
        )
