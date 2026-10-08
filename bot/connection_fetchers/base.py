from telegram import Update

from service import Connection

from ..context import Context

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..bot import Bot


class BaseConnectionFetcher(ABC):
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    @abstractmethod
    async def fetch(
        self, update: Update, context: Context
    ) -> list[Connection] | None: ...
