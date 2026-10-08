from telegram import Update

from core.enums import Mode
from core.settings import MODE
from service import Connection, ConnectionTargetObjectType, ServiceObject

from ..context import Context
from .api_request import APIRequestHandler
from .base import BaseHandler
from .condition import ConditionHandler
from .database_operation import DatabaseOperationHandler
from .invoice import InvoiceHandler
from .message import MessageHandler
from .randomizer import RandomizerHandler
from .temporary_variable import TemporaryVariableHandler
from .timer import TimerHandler
from .trigger import TriggerHandler

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
import asyncio
import logging

if TYPE_CHECKING:
    from ..bot import Bot

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _Processor:
    fetcher: Callable[[int], Awaitable[ServiceObject]]
    handler: BaseHandler[Any]


class ConnectionHandler(BaseHandler[Connection]):
    def __init__(self, bot: Bot) -> None:
        super().__init__(bot)
        self._processors: dict[ConnectionTargetObjectType, _Processor] = {
            ConnectionTargetObjectType.TRIGGER: _Processor(
                fetcher=self._bot.service.get_trigger, handler=TriggerHandler(self._bot)
            ),
            ConnectionTargetObjectType.MESSAGE: _Processor(
                fetcher=self._bot.service.get_message, handler=MessageHandler(self._bot)
            ),
            ConnectionTargetObjectType.CONDITION: _Processor(
                fetcher=self._bot.service.get_condition,
                handler=ConditionHandler(self._bot),
            ),
            ConnectionTargetObjectType.API_REQUEST: _Processor(
                fetcher=self._bot.service.get_api_request,
                handler=APIRequestHandler(self._bot),
            ),
            ConnectionTargetObjectType.DATABASE_OPERATION: _Processor(
                fetcher=self._bot.service.get_database_operation,
                handler=DatabaseOperationHandler(self._bot),
            ),
            ConnectionTargetObjectType.INVOICE: _Processor(
                fetcher=self._bot.service.get_invoice, handler=InvoiceHandler(self._bot)
            ),
            ConnectionTargetObjectType.TEMPORARY_VARIABLE: _Processor(
                fetcher=self._bot.service.get_temporary_variable,
                handler=TemporaryVariableHandler(self._bot),
            ),
            ConnectionTargetObjectType.TIMER: _Processor(
                fetcher=self._bot.service.get_timer, handler=TimerHandler(self._bot)
            ),
            ConnectionTargetObjectType.RANDOMIZER: _Processor(
                fetcher=self._bot.service.get_randomizer,
                handler=RandomizerHandler(self._bot),
            ),
        }

    async def handle(
        self, update: Update, connection: Connection, context: Context
    ) -> None:
        context = context.copy()
        processor: _Processor = self._processors[connection.target_object_type]

        obj: ServiceObject = await processor.fetcher(connection.target_object_id)
        connections: list[Connection] | None = await processor.handler.handle(
            update, obj, context
        )

        if not connections:
            return

        await self.handle_many(update, connections, context)

    async def handle_many(
        self, update: Update, connections: list[Connection], context: Context
    ) -> None:
        results: list[BaseException | None] = await asyncio.gather(
            *[self.handle(update, connection, context) for connection in connections],
            return_exceptions=True,
        )

        if MODE == Mode.DEBUG:
            for result, connection in zip(results, connections, strict=False):
                if isinstance(result, BaseException):
                    logger.error(
                        'Failed handling of connection (id=%d).',
                        connection.id,
                        exc_info=result,
                    )
