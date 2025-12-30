from telegram import BotCommand, Update, User
from telegram.constants import ParseMode, UpdateType
from telegram.ext import ApplicationBuilder, Defaults

from core.settings import SELF_URL, TELEGRAM_TOKEN
from core.storage import bots
from service import API
from service.models import Trigger

from .handler import Handler
from .request import ResilientHTTPXRequest
from .storage import Storage
from .tasks import TaskManager
from .utils.validation import is_valid_user

from typing import Final
import asyncio
import re
import string

COMMAND_CLEANUP_PATTERN: Final[re.Pattern[str]] = re.compile(f'[{string.punctuation}]')


class Bot:
    def __init__(self, service_id: int, token: str):
        self.app = (
            ApplicationBuilder()
            .token(token)
            .defaults(Defaults(parse_mode=ParseMode.HTML))
            .request(ResilientHTTPXRequest(read_timeout=20))
            .updater(None)
            .build()
        )
        self.telegram = self.app.bot
        self.service_id = service_id
        self.service_api = API(service_id)
        self.storage = Storage(bot_id=int(token.split(':')[0]))
        self.handler = Handler(self)
        self.task_manager = TaskManager(self)

    async def feed_webhook_update(self, update: Update) -> None:
        user: User | None = update.effective_user

        if not user or not await is_valid_user(self, user):
            return

        await self.app.update_queue.put(update)

    async def set_menu_commands(self) -> None:
        triggers: list[Trigger] = await self.service_api.get_triggers(
            has_command=True, has_command_payload=False, has_command_description=True
        )

        if not triggers:
            return

        await self.telegram.set_my_commands(
            [
                BotCommand(
                    command=COMMAND_CLEANUP_PATTERN.sub('', trigger.command.command),
                    description=trigger.command.description,
                )
                for trigger in triggers
                if trigger.command and trigger.command.description
            ]
        )

    async def start(self) -> None:
        self.app.add_handler(self.handler)

        await asyncio.gather(
            self.set_menu_commands(),
            self.telegram.set_webhook(
                f'{SELF_URL}/bots/{self.service_id}/webhook/',
                allowed_updates=[
                    UpdateType.MESSAGE,
                    UpdateType.CALLBACK_QUERY,
                    UpdateType.PRE_CHECKOUT_QUERY,
                ],
                secret_token=TELEGRAM_TOKEN,
            ),
        )

        await self.app.initialize()
        await self.app.start()
        await self.task_manager.start()

    async def stop(self) -> None:
        try:
            await self.telegram.delete_webhook()
        finally:
            del bots[self.service_id]
            await self.task_manager.stop()
            await self.app.stop()
            await self.app.shutdown()
