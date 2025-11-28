from telegram import BotCommand, Message, Update
from telegram.constants import ParseMode, UpdateType
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    Defaults,
    MessageHandler,
    filters,
)

from core.settings import SELF_URL, TELEGRAM_TOKEN
from core.storage import bots
from service import API
from service.models import Trigger

from .handlers.update import UpdateHandler
from .request import ResilientHTTPXRequest
from .tasks import TaskManager
from .utils import is_valid_user

from typing import Final
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
        self.update_handler = UpdateHandler(self)
        self.task_manager = TaskManager(self)
        self.last_messages: dict[int, list[Message]] = {}

    async def feed_webhook_update(self, update: Update) -> None:
        if not await is_valid_user(self, update.effective_user):
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
        await self.set_menu_commands()

        self.app.add_handler(MessageHandler(filters.TEXT, self.update_handler.handle))
        self.app.add_handler(CallbackQueryHandler(self.update_handler.handle))

        await self.telegram.set_webhook(
            f'{SELF_URL}/bots/{self.service_id}/webhook/',
            allowed_updates=[UpdateType.MESSAGE, UpdateType.CALLBACK_QUERY],
            secret_token=TELEGRAM_TOKEN,
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
