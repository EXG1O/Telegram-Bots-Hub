from telegram.client import TelegramClient
from telegram.enums import UpdateType
from telegram.exceptions import TelegramError
from telegram.models import BotCommand, Chat, Update, User

from core.enums import Mode
from core.settings import MODE, TELEGRAM_TOKEN
from core.storage import bots
from service.client import ServiceClient
from service.enums import ChatType as ServiceChatType
from service.models import Trigger
from service.schemas import BindUserToChat, CreateChat, CreateUser

from .background.manager import BackgroundTaskManager
from .handler import Handler
from .storage import Storage
from .utils.validation import is_subject_allowed

from collections.abc import Awaitable
from contextlib import suppress
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

    def __init__(self, service_id: int, token: str, webhook_url: str) -> None:
        self.token = token
        self.webhook_url = webhook_url
        self.telegram_id = int(token.split(':')[0])
        self.telegram = TelegramClient(bot_token=token)
        self.service_id = service_id
        self.service = ServiceClient(service_id)
        self.storage = Storage.for_bot(bot_id=self.telegram_id)
        self.handler = Handler(self)
        self.background_task_manager = BackgroundTaskManager(self)

    @property
    def me(self) -> User:
        if not self._me:
            raise RuntimeError('Bot is not started yet.')
        return self._me

    async def _is_update_allowed(self, update: Update) -> bool:
        chat: Chat | None = update.effective_chat

        if not chat:
            return False

        service_bot, service_chat, service_user = await asyncio.gather(
            self.service.get_bot(),
            self.service.create_chat(
                data=CreateChat(
                    telegram_id=chat.id,
                    type=ServiceChatType(chat.type),
                    title=chat.title,
                    username=chat.username,
                    first_name=chat.first_name,
                    last_name=chat.last_name,
                    is_forum=chat.is_forum,
                    is_direct_messages=chat.is_direct_messages,
                )
            ),
            self.service.create_user(
                data=CreateUser(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    is_bot=user.is_bot,
                    is_premium=user.is_premium,
                )
            )
            if (user := update.effective_user)
            else asyncio.sleep(0),
        )

        if service_user:
            await asyncio.create_task(
                self.service.bind_users_to_chat(
                    id=service_chat.id, data=[BindUserToChat(id=service_user.id)]
                )
            )

        return is_subject_allowed(
            service_bot=service_bot, service_subject=service_chat
        ) and (
            not service_user
            or is_subject_allowed(service_bot=service_bot, service_subject=service_user)
        )

    async def feed_webhook_update(self, update: Update) -> None:
        if not await self._is_update_allowed(update):
            return

        task: Awaitable[None] = self.handler.handle_update(update)

        if MODE == Mode.DEBUG:
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

    async def _set_menu_commands(self) -> None:
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
            self._set_menu_commands(),
            self.telegram.set_webhook(
                self.webhook_url,
                allowed_updates=[
                    UpdateType.MESSAGE,
                    UpdateType.CALLBACK_QUERY,
                    UpdateType.PRE_CHECKOUT_QUERY,
                ],
                secret_token=TELEGRAM_TOKEN,
            ),
        )
        await self.background_task_manager.start()
        await self.service.assign_to_hub()

    async def stop(self) -> None:
        try:
            with suppress(TelegramError):
                await self.telegram.delete_webhook()
            del bots[self.service_id]
            await self.background_task_manager.stop()
        finally:
            await self.service.unassign_from_hub()
