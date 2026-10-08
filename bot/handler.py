from telegram import Update

from service import Connection

from .connection_fetchers import (
    InvoiceConnectionFetcher,
    MessageKeyboardButtonConnectionFetcher,
    SubscriptionMessageKeyboardButtonConnectionFetcher,
    SubscriptionTriggerConnectionFetcher,
    TriggerConnectionFetcher,
)
from .connection_fetchers.base import BaseConnectionFetcher
from .context import Context
from .handlers import ConnectionHandler

from typing import TYPE_CHECKING
import asyncio
import logging

if TYPE_CHECKING:
    from .bot import Bot

logger = logging.getLogger(__name__)


class Handler:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._connection_handler = ConnectionHandler(self._bot)
        self._connection_fetchers: list[BaseConnectionFetcher] = [
            TriggerConnectionFetcher(self._bot),
            MessageKeyboardButtonConnectionFetcher(self._bot),
            InvoiceConnectionFetcher(self._bot),
        ]
        self._subscription_connection_fetchers: list[BaseConnectionFetcher] = [
            SubscriptionTriggerConnectionFetcher(self._bot),
            SubscriptionMessageKeyboardButtonConnectionFetcher(self._bot),
        ]

    async def _run_fetcher(
        self, fetcher: BaseConnectionFetcher, update: Update, context: Context
    ) -> bool:
        result: bool = False
        try:
            connections: list[Connection] | None = await fetcher.fetch(update, context)
            if connections:
                result = True
                await self._connection_handler.handle_many(update, connections, context)
        except Exception:
            logger.exception(
                'Unexpected error processing fetcher %s for update (update_id=%d).',
                fetcher.__class__.__name__,
                update.update_id,
            )
        return result

    async def handle_update(self, update: Update) -> None:
        if update.pre_checkout_query:
            await self._bot.telegram.answer_pre_checkout_query(
                pre_checkout_query_id=update.pre_checkout_query.id, ok=True
            )
            return

        context = Context(self._bot, update)

        if any(
            await asyncio.gather(
                *[
                    self._run_fetcher(fetcher, update, context)
                    for fetcher in self._subscription_connection_fetchers
                ]
            )
        ):
            return

        async with asyncio.TaskGroup() as group:
            for fetcher in self._connection_fetchers:
                group.create_task(self._run_fetcher(fetcher, update, context))
