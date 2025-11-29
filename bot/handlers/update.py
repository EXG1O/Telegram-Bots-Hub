from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.ext import ContextTypes

from service.models import CommandKeyboardButton, Connection, Trigger

from ..storage import EventStorage
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
            Callable[
                [Update, EventStorage, Variables], Awaitable[list[Connection] | None]
            ]
        ] = [
            self._get_wait_trigger_connections,
            self._get_trigger_connections,
            self._get_command_keyboard_button_connections,
        ]

    async def _get_wait_trigger_connections(
        self, update: Update, event_storage: EventStorage, variables: Variables
    ) -> list[Connection] | None:
        if not event_storage.user:
            return None

        message: Message | None = update.effective_message

        if not message or not message.text:
            return None

        trigger_id: int | None = await event_storage.user.get('expected_trigger_id')

        if not trigger_id:
            return None

        trigger: Trigger = await self.bot.service_api.get_trigger(id=trigger_id)
        connections: list[Connection] = []

        if trigger.command and message.text.startswith('/') and len(message.text) > 1:
            command, _, payload = message.text.removeprefix('/').partition(' ')

            if (
                trigger.command.payload and payload != trigger.command.payload
            ) or command != trigger.command.command:
                return None

            connections = trigger.source_connections
        elif (
            trigger.message
            and trigger.message.text
            and (
                message.text
                == (await replace_text_variables(trigger.message.text, variables))
            )
        ):
            connections = trigger.source_connections
        elif trigger.message and not trigger.message.text:
            connections = trigger.source_connections
        else:
            return None

        await event_storage.user.delete('expected_trigger_id')

        return connections

    async def _get_command_triggers(self, message_text: str) -> list[Trigger] | None:
        if not message_text.startswith('/') or len(message_text) == 1:
            return None

        command, _, payload = message_text.removeprefix('/').partition(' ')

        return await self.bot.service_api.get_triggers(
            command=command,
            command_payload=payload or None,
            has_command_payload=bool(payload),
        )

    async def _get_message_triggers(
        self, message_text: str, variables: Variables
    ) -> list[Trigger] | None:
        (
            triggers_with_message_text,
            triggers_without_message_text,
        ) = await asyncio.gather(
            self.bot.service_api.get_triggers(
                has_message=True, has_message_text=True, has_target_connections=False
            ),
            self.bot.service_api.get_triggers(
                has_message=True, has_message_text=False, has_target_connections=False
            ),
        )

        if not triggers_with_message_text and not triggers_without_message_text:
            return None

        trigger_message_texts: list[str] = await asyncio.gather(
            *[
                replace_text_variables(
                    trigger.message.text,  # type: ignore [union-attr, arg-type]
                    variables,
                )
                for trigger in triggers_with_message_text
            ]
        )

        return [
            trigger
            for trigger, trigger_message_text in zip(
                triggers_with_message_text, trigger_message_texts, strict=False
            )
            if message_text == trigger_message_text
        ] + triggers_without_message_text

    async def _get_trigger_connections(
        self, update: Update, event_storage: EventStorage, variables: Variables
    ) -> list[Connection] | None:
        message: Message | None = update.effective_message

        if not message or not message.text:
            return None

        return list(
            chain.from_iterable(
                trigger.source_connections
                for trigger in chain.from_iterable(
                    filter(
                        None,
                        await asyncio.gather(
                            self._get_command_triggers(message.text),
                            self._get_message_triggers(message.text, variables),
                        ),
                    )
                )
            )
        )

    async def _get_command_keyboard_button_connections(
        self, update: Update, event_storage: EventStorage, variables: Variables
    ) -> list[Connection] | None:
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
        else:
            return None

        return list(
            chain.from_iterable(button.source_connections for button in buttons)
        )

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat: Chat | None = update.effective_chat
        user: User | None = update.effective_user

        event_storage = EventStorage(
            bot_id=self.bot.telegram.id,
            chat_id=user.id if user else None,
            user_id=chat.id if chat else None,
        )
        variables = Variables(self.bot, update.effective_user, update.effective_message)

        await self.connection_handler.handle_many(
            update,
            list(
                chain.from_iterable(
                    filter(
                        None,
                        await asyncio.gather(
                            *[
                                fetcher(update, event_storage, variables)
                                for fetcher in self.connection_fetchers
                            ]
                        ),
                    )
                )
            ),
            event_storage,
            variables,
        )
