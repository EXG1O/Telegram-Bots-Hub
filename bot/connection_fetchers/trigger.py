from telegram import Message, Update

from service import Connection, Trigger

from ..context import Context
from ..utils.variables import replace_text_variables
from ..variables import Variables
from .base import BaseConnectionFetcher

from itertools import chain
import asyncio


class TriggerConnectionFetcher(BaseConnectionFetcher):
    async def _get_command_triggers(self, message_text: str) -> list[Trigger] | None:
        if (
            not message_text.startswith('/')
            or len(message_text) == 1
            or len(message_text) > 32
        ):
            return None

        command, _, payload = message_text.removeprefix('/').partition(' ')

        return await self._bot.service.get_triggers(
            command=command,
            command_payload=payload or None,
            has_command_payload=bool(payload),
            has_source_connections=True,
        )

    async def _get_message_triggers(
        self, message_text: str, variables: Variables
    ) -> list[Trigger] | None:
        (
            triggers_with_message_text,
            triggers_without_message_text,
        ) = await asyncio.gather(
            self._bot.service.get_triggers(
                has_message=True,
                has_message_text=True,
                has_source_connections=True,
                has_target_connections=False,
            ),
            self._bot.service.get_triggers(
                has_message=True,
                has_message_text=False,
                has_source_connections=True,
                has_target_connections=False,
            ),
        )

        if not (triggers_with_message_text or triggers_without_message_text):
            return None

        trigger_message_texts: list[str] = await asyncio.gather(
            *[
                replace_text_variables(trigger_message_text, variables)
                for trigger in triggers_with_message_text
                if (
                    (trigger_message := trigger.message)
                    and (trigger_message_text := trigger_message.text)
                )
            ]
        )

        return [
            trigger
            for trigger, trigger_message_text in zip(
                triggers_with_message_text, trigger_message_texts, strict=False
            )
            if message_text == trigger_message_text
        ] + triggers_without_message_text

    async def fetch(self, update: Update, context: Context) -> list[Connection] | None:
        message: Message | None = update.message

        if not (
            message and (user := message.user) and user.id != self._bot.telegram_id
        ):
            return None

        message_text: str | None = message.text

        if not message_text:
            return None

        return list(
            chain.from_iterable(
                trigger.source_connections
                for trigger in chain.from_iterable(
                    filter(
                        None,
                        await asyncio.gather(
                            self._get_command_triggers(message_text),
                            self._get_message_triggers(message_text, context.variables),
                        ),
                    )
                )
            )
        )
