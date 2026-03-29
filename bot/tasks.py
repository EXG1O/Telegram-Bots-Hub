from telegram.enums import ChatType
from telegram.exceptions import InvalidTokenError
from telegram.models import Chat, Update, User

from service.models import BackgroundTask
from service.models import Bot as ServiceBot
from service.models import User as ServiceUser

from .context import HandlerContext
from .storage.models import BotStorageData
from .utils.validation import is_valid_user

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
import asyncio
import logging

if TYPE_CHECKING:
    from ..bot import Bot
else:
    Bot = Any

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.tasks: set[asyncio.Task[Any]] = set()

    async def _monitor_token(self) -> None:
        try:
            while True:
                await asyncio.sleep(86400)
                await self.bot.telegram.get_me()
        except InvalidTokenError:
            await self.bot.stop()

    async def _handle_background_task(
        self,
        service_bot: ServiceBot,
        service_user: ServiceUser,
        task: BackgroundTask,
    ) -> None:
        if not await is_valid_user(
            self.bot, service_bot=service_bot, service_user=service_user
        ):
            return

        user_first_name: str = service_user.full_name[:64]
        user_last_name: str = service_user.full_name[64:]

        chat = Chat(
            id=service_user.telegram_id,
            type=ChatType.PRIVATE,
            first_name=user_first_name,
            last_name=user_last_name,
        )
        user = User(
            id=service_user.telegram_id,
            is_bot=False,
            first_name=user_first_name,
            last_name=user_last_name,
        )

        update = Update(update_id=0)
        update._effective_chat = chat
        update._effective_user = user

        await self.bot.handler.connection_handler.handle_many(
            update, task.source_connections, HandlerContext(self.bot, update)
        )

    async def _process_background_tasks(self) -> None:
        while True:
            await asyncio.sleep(3600)

            tasks: list[BackgroundTask] = await self.bot.service.get_background_tasks()

            if not tasks:
                continue

            service_bot: ServiceBot | None = None
            service_users: list[ServiceUser] | None = None

            storage_data: BotStorageData = await self.bot.storage.get_data()
            last_completed_tasks: dict[int, datetime] = (
                storage_data.completed_background_tasks
            )

            completed_tasks: dict[int, datetime] = {}
            current_datetime: datetime = datetime.now(UTC)

            for task in tasks:
                if not (
                    last_completed_task_datetime := last_completed_tasks.get(task.id)
                ) or (
                    (last_completed_task_datetime + timedelta(days=task.interval.value))
                    > current_datetime
                ):
                    completed_tasks[task.id] = (
                        last_completed_task_datetime or current_datetime
                    )
                    continue

                if service_users is None:
                    service_users = await self.bot.service.get_users()

                if not service_users:
                    break

                if service_bot is None:
                    service_bot = await self.bot.service.get_bot()

                results: list[BaseException | None] = await asyncio.gather(
                    *[
                        self._handle_background_task(service_bot, service_user, task)
                        for service_user in service_users
                    ],
                    return_exceptions=True,
                )

                if logger.isEnabledFor(logging.DEBUG):
                    for result, service_user in zip(
                        results, service_users, strict=False
                    ):
                        if isinstance(result, BaseException):
                            logger.debug(
                                (
                                    'Failed handling of background task (id=%s) '
                                    'for user (service_id=%s).'
                                ),
                                task.id,
                                service_user.id,
                                exc_info=result,
                            )

                completed_tasks[task.id] = current_datetime

            async with self.bot.storage.transaction() as storage_data:
                storage_data.completed_background_tasks = completed_tasks

    async def start(self) -> None:
        self.tasks.add(asyncio.create_task(self._monitor_token()))
        self.tasks.add(asyncio.create_task(self._process_background_tasks()))

    async def stop(self) -> None:
        for task in self.tasks:
            task.cancel()
