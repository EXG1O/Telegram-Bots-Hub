from telegram import Message, Update

from service import Connection, Trigger

from ...context import Context
from ...storage import Storage, SubscriptionType, UserStorageData
from ...utils.variables import replace_text_variables
from ..base import BaseConnectionFetcher

import asyncio


class SubscriptionTriggerConnectionFetcher(BaseConnectionFetcher):
    async def fetch(self, update: Update, context: Context) -> list[Connection] | None:
        message: Message | None = update.message
        user_storage: Storage[UserStorageData] | None = context.user_storage

        if not (
            message
            and (user := message.user)
            and user.id != self._bot.telegram_id
            and user_storage
        ):
            return None

        message_text: str | None = message.text

        if not message_text:
            return None

        storage_data: UserStorageData = await user_storage.get_data()
        trigger_ids: set[int] = storage_data.subscriptions[SubscriptionType.TRIGGER]

        if not trigger_ids:
            return None

        triggers: list[Trigger] = await self._bot.service.get_triggers(ids=trigger_ids)
        trigger_message_texts: list[str | None] = await asyncio.gather(
            *[
                replace_text_variables(trigger_message_text, context.variables)
                if (trigger_message := trigger.message)
                and (trigger_message_text := trigger_message.text)
                else asyncio.sleep(0)
                for trigger in triggers
            ]
        )
        connections: list[Connection] = []

        for trigger, trigger_message_text in zip(
            triggers, trigger_message_texts, strict=True
        ):
            if (
                (trigger_command := trigger.command)
                and message_text.startswith('/')
                and len(message_text) > 1
            ):
                command, _, payload = message_text.removeprefix('/').partition(' ')

                if command == trigger_command.command and (
                    not trigger_command.payload or payload == trigger_command.payload
                ):
                    connections.extend(trigger.source_connections)
            elif trigger_message_text and message_text == trigger_message_text:
                connections.extend(trigger.source_connections)

        async with user_storage.transaction() as storage_data:
            storage_data.subscriptions[SubscriptionType.TRIGGER] = set()

        return connections
