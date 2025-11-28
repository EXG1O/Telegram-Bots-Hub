from telegram import Chat, Update, User
from telegram.error import InvalidToken

import service.models

from .storage import EventStorage
from .utils import is_valid_user
from .variables import Variables

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
import asyncio

if TYPE_CHECKING:
    from ..bot import Bot
else:
    Bot = Any


class TaskManager:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.tasks: set[asyncio.Task[Any]] = set()

    async def _monitor_token(self) -> None:
        try:
            while self.bot.app.running:
                await asyncio.sleep(86400)
                await self.bot.telegram.get_me()
        except InvalidToken:
            await self.bot.stop()

    async def _handle_background_task(
        self,
        bot: service.models.Bot,
        user: service.models.User,
        task: service.models.BackgroundTask,
    ) -> None:
        if not await is_valid_user(self.bot, service_bot=bot, service_user=user):
            return

        user_first_name: str = user.full_name[:64]
        user_last_name: str = user.full_name[64:]

        update = Update(update_id=0)
        update._effective_user = User(
            id=user.telegram_id,
            first_name=user_first_name,
            last_name=user_last_name,
            is_bot=False,
        )
        update._effective_chat = Chat(
            id=user.telegram_id,
            type=Chat.PRIVATE,
            first_name=user_first_name,
            last_name=user_last_name,
        )

        await self.bot.update_handler.connection_handler.handle_many(
            update,
            task.source_connections,
            EventStorage(
                bot_id=self.bot.telegram.id,
                chat_id=user.telegram_id,
                user_id=user.telegram_id,
            ),
            Variables(self.bot, update.effective_user),
        )

    async def _process_background_tasks(self) -> None:
        while self.bot.app.running:
            await asyncio.sleep(3600)

            tasks: list[
                service.models.BackgroundTask
            ] = await self.bot.service_api.get_background_tasks()

            if not tasks:
                continue

            bot: service.models.Bot | None = None
            users: list[service.models.User] | None = None
            current_datetime: datetime = datetime.now(UTC)
            background_tasks: dict[str, str] = await self.bot.storage.get(
                'background_tasks', {}
            )

            for task in tasks:
                try:
                    if (
                        datetime.fromisoformat(
                            background_tasks.setdefault(
                                str(task.id), datetime.isoformat(current_datetime)
                            )
                        )
                        + timedelta(days=task.interval.value)
                    ) > current_datetime:
                        continue

                    if not bot:
                        bot = await self.bot.service_api.get_bot()
                    if users is None:
                        users = await self.bot.service_api.get_users()

                    await asyncio.gather(
                        *[
                            self._handle_background_task(bot, user, task)
                            for user in users
                        ]
                    )

                    background_tasks[str(task.id)] = datetime.isoformat(
                        current_datetime
                    )
                except Exception:
                    pass  # FIXME: In the future, error logging will be added here.

            await self.bot.storage.set(
                'background_tasks',
                background_tasks,
                expiry=2592000,  # 30 days
            )

    async def start(self) -> None:
        self.tasks.add(asyncio.create_task(self._monitor_token()))
        self.tasks.add(asyncio.create_task(self._process_background_tasks()))

    async def stop(self) -> None:
        for task in self.tasks:
            task.cancel()
