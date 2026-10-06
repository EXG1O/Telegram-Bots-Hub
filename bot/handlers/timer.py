from telegram import Update

from service import Connection, Timer

from ..context import HandlerContext
from .base import BaseHandler

import asyncio


class TimerHandler(BaseHandler[Timer]):
    async def handle(
        self, update: Update, timer: Timer, context: HandlerContext
    ) -> list[Connection]:
        await asyncio.sleep(timer.duration_seconds)
        return timer.source_connections
