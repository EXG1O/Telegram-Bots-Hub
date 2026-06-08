from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...bot import Bot
else:
    Bot = Any


class BackgroundTask(ABC):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @abstractmethod
    async def __call__(self) -> None: ...
