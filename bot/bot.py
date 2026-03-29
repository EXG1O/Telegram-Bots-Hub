from telegram.client import TelegramClient
from telegram.enums import UpdateType
from telegram.models import BotCommand, Update, User

from core.settings import DEBUG, SELF_URL, TELEGRAM_TOKEN
from core.storage import bots
from service.client import ServiceClient
from service.models import Trigger

from .handler import Handler
from .storage import Storage
from .tasks import TaskManager
from .utils.validation import is_valid_user

from collections.abc import Awaitable
from typing import Final
import asyncio
import logging
import re
import string
import time

logger = logging.getLogger(__name__)


COMMAND_CLEANUP_PATTERN: Final[re.Pattern[str]] = re.compile(f'[{string.punctuation}]')


class Bot:
    _me: User | None = None

    def __init__(self, service_id: int, token: str):
        self.token = token
        self.telegram_id = int(token.split(':')[0])
        self.telegram = TelegramClient(bot_token=token)
        self.service_id = service_id
        self.service = ServiceClient(service_id)
        self.storage = Storage.for_bot(bot_id=self.telegram_id)
        self.handler = Handler(self)
        self.task_manager = TaskManager(self)

    @property
    def me(self) -> User:
        if not self._me:
            raise RuntimeError('Bot is not started yet.')
        return self._me

    async def feed_webhook_update(self, update: Update) -> None:
        if not (
            (user := update.effective_user)
            and (user.id == self.telegram_id or await is_valid_user(self, user=user))
        ):
            return

        task: Awaitable[None] = self.handler.handle_update(update)

        if DEBUG:
            start_time: float = time.perf_counter()
            await task
            elapsed_time: float = time.perf_counter() - start_time
            logger.debug(
                'Processing of update (id=%s) completed in %s ms.',
                update.update_id,
                round(elapsed_time * 1000, 3),
            )
        else:
            await task

    async def set_menu_commands(self) -> None:
        triggers: list[Trigger] = await self.service.get_triggers(
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
        self._me, *_ = await asyncio.gather(
            self.telegram.get_me(),
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
        await self.task_manager.start()

    async def stop(self) -> None:
        try:
            await self.telegram.delete_webhook()
        finally:
            del bots[self.service_id]
            await self.task_manager.stop()
