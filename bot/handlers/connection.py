from telegram import Update

from service.enums import ConnectionTargetObjectType
from service.models import Connection

from ..storage import EventStorage
from ..variables import Variables
from .api_request import APIRequestHandler
from .base import BaseHandler
from .command import CommandHandler
from .condition import ConditionHandler
from .database_operation import DatabaseOperationHandler
from .trigger import TriggerHandler

from collections.abc import Awaitable, Callable
from copy import copy
from typing import TYPE_CHECKING, Any
import asyncio

if TYPE_CHECKING:
    from ..bot import Bot
else:
    Bot = Any


class ConnectionHandler(BaseHandler[Connection]):
    def __init__(self, bot: Bot) -> None:
        super().__init__(bot)
        self.fetchers: dict[
            ConnectionTargetObjectType, Callable[[int], Awaitable[Any]]
        ] = {
            ConnectionTargetObjectType.TRIGGER: (
                lambda id: self.bot.service_api.get_trigger(id)
            ),
            ConnectionTargetObjectType.COMMAND: (
                lambda id: self.bot.service_api.get_command(id)
            ),
            ConnectionTargetObjectType.CONDITION: (
                lambda id: self.bot.service_api.get_condition(id)
            ),
            ConnectionTargetObjectType.API_REQUEST: (
                lambda id: self.bot.service_api.get_api_request(id)
            ),
            ConnectionTargetObjectType.DATABASE_OPERATION: (
                lambda id: self.bot.service_api.get_database_operation(id)
            ),
        }
        self.handlers: dict[ConnectionTargetObjectType, BaseHandler[Any]] = {
            ConnectionTargetObjectType.TRIGGER: TriggerHandler(self.bot),
            ConnectionTargetObjectType.COMMAND: CommandHandler(self.bot),
            ConnectionTargetObjectType.CONDITION: ConditionHandler(self.bot),
            ConnectionTargetObjectType.API_REQUEST: APIRequestHandler(self.bot),
            ConnectionTargetObjectType.DATABASE_OPERATION: DatabaseOperationHandler(
                self.bot
            ),
        }

    async def handle(
        self,
        update: Update,
        connection: Connection,
        event_storage: EventStorage,
        variables: Variables,
    ) -> None:
        variables = copy(variables)
        object: Any = await self.fetchers[connection.target_object_type](
            connection.target_object_id
        )
        connections: list[Connection] | None = await self.handlers[
            connection.target_object_type
        ].handle(update, object, event_storage, variables)

        if not connections:
            return

        await self.handle_many(update, connections, event_storage, variables)

    async def handle_many(
        self,
        update: Update,
        connections: list[Connection],
        event_storage: EventStorage,
        variables: Variables,
    ) -> None:
        await asyncio.gather(
            *[
                self.handle(update, connection, event_storage, variables)
                for connection in connections
            ]
        )
