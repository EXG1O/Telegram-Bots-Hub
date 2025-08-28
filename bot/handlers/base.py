from telegram import Update

from service.models import Connection

from ..variables import Variables

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..bot import Bot
else:
    Bot = Any


class BaseHandler[T](ABC):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @abstractmethod
    async def handle(
        self, update: Update, obj: T, variables: Variables
    ) -> list[Connection] | None: ...
