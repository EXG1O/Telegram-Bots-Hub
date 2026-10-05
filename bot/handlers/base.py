from telegram import Update

from service import Connection, ServiceObject

from ..context import HandlerContext

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..bot import Bot


class BaseHandler[T: ServiceObject](ABC):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @abstractmethod
    async def handle(
        self, update: Update, obj: T, context: HandlerContext
    ) -> list[Connection] | None: ...
