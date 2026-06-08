from telegram.exceptions import InvalidTokenError

from .base import BackgroundTask


class MonitorTokenTask(BackgroundTask):
    async def __call__(self) -> None:
        try:
            await self.bot.telegram.get_me()
        except InvalidTokenError:
            await self.bot.stop()
