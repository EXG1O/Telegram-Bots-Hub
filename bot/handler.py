from telegram.models import Message, Update

from service.models import Connection, MessageKeyboardButton, Trigger

from .context import HandlerContext
from .handlers.connection import ConnectionHandler
from .storage import Storage
from .utils.variables import replace_text_variables
from .variables import Variables

from collections.abc import Awaitable, Callable, Sequence
from itertools import chain
from typing import TYPE_CHECKING, Any
import asyncio

if TYPE_CHECKING:
    from .bot import Bot
else:
    Bot = Any


class Handler:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.connection_handler = ConnectionHandler(self.bot)
        self.connection_fetchers: Sequence[
            Callable[[Update, HandlerContext], Awaitable[list[Connection] | None]]
        ] = [
            self._get_wait_trigger_connections,
            self._get_trigger_connections,
            self._get_command_keyboard_button_connections,
        ]

    async def _get_wait_trigger_connections(
        self, update: Update, context: HandlerContext
    ) -> list[Connection] | None:
        message: Message | None = update.message
        user_storage: Storage | None = context.user_storage

        if not (
            message
            and (user := message.user)
            and user.id != self.bot.telegram_id
            and message.text
            and user_storage
        ):
            return None

        trigger_id: int | None = await user_storage.get('expected_trigger_id')

        if not trigger_id:
            return None

        trigger: Trigger = await self.bot.service.get_trigger(id=trigger_id)

        if TYPE_CHECKING:
            connections: list[Connection]

        if (
            (trigger_command := trigger.command)
            and message.text.startswith('/')
            and len(message.text) > 1
        ):
            command, _, payload = message.text.removeprefix('/').partition(' ')

            if not (
                command == trigger_command.command
                and (not trigger_command.payload or payload == trigger_command.payload)
            ):
                return None

            connections = trigger.source_connections
        elif (trigger_message := trigger.message) and (
            not trigger_message.text
            or (
                message.text
                == await replace_text_variables(trigger_message.text, context.variables)
            )
        ):
            connections = trigger.source_connections
        else:
            return None

        await user_storage.delete('expected_trigger_id')

        return connections

    async def _get_command_triggers(self, message_text: str) -> list[Trigger] | None:
        if not message_text.startswith('/') or len(message_text) == 1:
            return None

        command, _, payload = message_text.removeprefix('/').partition(' ')

        return await self.bot.service.get_triggers(
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
            self.bot.service.get_triggers(
                has_message=True, has_message_text=True, has_target_connections=False
            ),
            self.bot.service.get_triggers(
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
        self, update: Update, context: HandlerContext
    ) -> list[Connection] | None:
        message: Message | None = update.message

        if not (
            message
            and (user := message.user)
            and user.id != self.bot.telegram_id
            and message.text
        ):
            return None

        return list(
            chain.from_iterable(
                trigger.source_connections
                for trigger in chain.from_iterable(
                    filter(
                        None,
                        await asyncio.gather(
                            self._get_command_triggers(message.text),
                            self._get_message_triggers(message.text, context.variables),
                        ),
                    )
                )
            )
        )

    async def _get_command_keyboard_button_connections(
        self, update: Update, context: HandlerContext
    ) -> list[Connection] | None:
        buttons: list[MessageKeyboardButton] = []

        if (
            (callback_query := update.callback_query)
            and callback_query.data
            and callback_query.data.isdigit()
        ):
            buttons = await self.bot.service.get_messages_keyboard_buttons(
                id=int(callback_query.data)
            )
        elif (message := update.message) and message.text:
            buttons = await self.bot.service.get_messages_keyboard_buttons(
                text=message.text
            )
        else:
            return None

        return list(
            chain.from_iterable(button.source_connections for button in buttons)
        )

    async def handle_update(self, update: Update) -> None:
        if update.pre_checkout_query:
            await self.bot.telegram.answer_pre_checkout_query(
                pre_checkout_query_id=update.pre_checkout_query.id, ok=True
            )
            return

        context = HandlerContext(self.bot, update)

        await self.connection_handler.handle_many(
            update,
            list(
                chain.from_iterable(
                    filter(
                        None,
                        await asyncio.gather(
                            *[
                                fetcher(update, context)
                                for fetcher in self.connection_fetchers
                            ]
                        ),
                    )
                )
            ),
            context,
        )
