from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.ext import Application, BaseHandler, ContextTypes, filters
from telegram.ext._utils.types import FilterDataDict

from service.models import Connection, MessageKeyboardButton, Trigger

from .handlers.connection import ConnectionHandler
from .storage import EventStorage
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


class Handler(BaseHandler[Update, ContextTypes.DEFAULT_TYPE, None]):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.block: bool = True
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
        event_message: Message | None = update.effective_message
        callback_query: CallbackQuery | None = update.callback_query

        buttons: list[MessageKeyboardButton] = []

        if callback_query and callback_query.data and callback_query.data.isdigit():
            buttons = await self.bot.service_api.get_messages_keyboard_buttons(
                id=int(callback_query.data)
            )
        elif event_message and event_message.text:
            buttons = await self.bot.service_api.get_messages_keyboard_buttons(
                text=event_message.text
            )
        else:
            return None

        return list(
            chain.from_iterable(button.source_connections for button in buttons)
        )

    def check_update(self, update: object) -> bool | None:
        if not isinstance(update, Update):
            return None

        result: FilterDataDict | bool | None = filters.TEXT.check_update(update)

        if result:
            return bool(result)
        elif update.callback_query or update.pre_checkout_query:
            return True

        return False

    async def handle_update(
        self,
        update: Update,
        application: Application[Any, ContextTypes.DEFAULT_TYPE, Any, Any, Any, Any],
        check_result: object,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        if update.pre_checkout_query:
            await update.pre_checkout_query.answer(ok=True)
            return

        chat: Chat | None = update.effective_chat
        user: User | None = update.effective_user

        event_storage = EventStorage(
            bot_id=self.bot.telegram.id,
            chat_id=user.id if user else None,
            user_id=chat.id if chat else None,
        )
        variables = Variables(
            bot=self.bot,
            chat=update.effective_chat,
            user=update.effective_user,
            message=update.effective_message,
        )

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
