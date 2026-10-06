from telegram import Update

from service import Connection, Randomizer

from ..context import HandlerContext
from .base import BaseHandler

import random


class RandomizerHandler(BaseHandler[Randomizer]):
    async def handle(
        self, update: Update, randomizer: Randomizer, context: HandlerContext
    ) -> list[Connection] | None:
        if not randomizer.source_connections:
            return None
        return [random.choice(randomizer.source_connections)]
