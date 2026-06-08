from core.settings import (
    BOT_BACKGROUND_MONITOR_TOKEN_INTERVAL,
    BOT_BACKGROUND_PROCESS_SERVICE_TASKS_INTERVAL,
)

from .tasks import MonitorTokenTask, ProcessServiceTasksTask

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any
import asyncio
import logging

if TYPE_CHECKING:
    from ..bot import Bot
else:
    Bot = Any


logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._tasks: set[asyncio.Task[None]] = set()

    async def _run_task(
        self, func: Callable[[], Awaitable[None]], interval: int
    ) -> None:
        while True:
            await asyncio.sleep(interval)
            try:
                await func()
            except Exception:
                logger.exception('Background task %s failed.', func.__class__.__name__)

    async def start(self) -> None:
        self._tasks.update(
            {
                asyncio.create_task(
                    self._run_task(
                        MonitorTokenTask(self.bot),
                        BOT_BACKGROUND_MONITOR_TOKEN_INTERVAL,
                    )
                ),
                asyncio.create_task(
                    self._run_task(
                        ProcessServiceTasksTask(self.bot),
                        BOT_BACKGROUND_PROCESS_SERVICE_TASKS_INTERVAL,
                    )
                ),
            }
        )

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
