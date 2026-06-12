from telegram.enums import ChatType
from telegram.models import Chat, Update, User

from core.enums import Mode
from core.settings import MODE
from service.models import BackgroundTask as ServiceBackgroundTask
from service.models import Bot as ServiceBot
from service.models import Pagination
from service.models import User as ServiceUser

from ...context import HandlerContext
from ...storage.models import BotStorageData
from ...utils.validation import is_valid_user
from .base import BackgroundTask

from datetime import UTC, datetime, timedelta
from itertools import batched
import asyncio
import logging

logger = logging.getLogger(__name__)


class ProcessServiceTasksTask(BackgroundTask):
    async def _handle_task(
        self,
        service_bot: ServiceBot,
        service_user: ServiceUser,
        task: ServiceBackgroundTask,
    ) -> None:
        if not await is_valid_user(
            self.bot, service_bot=service_bot, service_user=service_user
        ):
            return

        update = Update(update_id=0)
        update._effective_chat = Chat(
            id=service_user.telegram_id,
            type=ChatType.PRIVATE,
            username=service_user.username,
            first_name=service_user.first_name,
            last_name=service_user.last_name,
        )
        update._effective_user = User(
            id=service_user.telegram_id,
            username=service_user.username,
            first_name=service_user.first_name,
            last_name=service_user.last_name,
            is_bot=service_user.is_bot,
            is_premium=service_user.is_premium,
        )

        await self.bot.handler.connection_handler.handle_many(
            update, task.source_connections, HandlerContext(self.bot, update)
        )

    def _should_skip_task(
        self,
        task: ServiceBackgroundTask,
        last_completed_tasks: dict[int, datetime],
        current_datetime: datetime,
    ) -> tuple[bool, datetime]:
        last_completed_task_datetime: datetime | None = last_completed_tasks.get(
            task.id
        )

        if last_completed_task_datetime is None:
            return True, current_datetime

        interval: timedelta = (
            timedelta(seconds=1)
            if MODE == Mode.DEBUG
            else timedelta(days=task.interval.value)
        )

        if last_completed_task_datetime + interval > current_datetime:
            return True, last_completed_task_datetime

        return False, current_datetime

    async def __call__(self) -> None:
        tasks: list[
            ServiceBackgroundTask
        ] = await self.bot.service.get_background_tasks(has_source_connections=True)

        if not tasks:
            return

        storage_data: BotStorageData = await self.bot.storage.get_data()
        last_completed_tasks: dict[int, datetime] = (
            storage_data.completed_background_tasks
        )

        active_tasks: list[ServiceBackgroundTask] = []
        completed_tasks: dict[int, datetime] = {}
        current_datetime: datetime = datetime.now(UTC)

        for task in tasks:
            should_skip_task, completed_task_datetime = self._should_skip_task(
                task, last_completed_tasks, current_datetime
            )

            if should_skip_task:
                completed_tasks[task.id] = completed_task_datetime
            else:
                active_tasks.append(task)

        if not active_tasks:
            async with self.bot.storage.transaction() as storage_data:
                storage_data.completed_background_tasks.update(completed_tasks)
            return

        service_bot: ServiceBot = await self.bot.service.get_bot()

        limit: int = 250
        offset: int = 0

        while True:
            pagination: Pagination[ServiceUser] = await self.bot.service.get_users(
                limit=limit, offset=offset
            )
            service_users: list[ServiceUser] = pagination.results

            if not service_users:
                break

            for task in active_tasks:
                for service_user_batch in batched(service_users, 15, strict=False):
                    results: list[BaseException | None] = await asyncio.gather(
                        *[
                            self._handle_task(service_bot, service_user, task)
                            for service_user in service_user_batch
                        ],
                        return_exceptions=True,
                    )

                if MODE == Mode.DEBUG:
                    for result, service_user in zip(
                        results, service_user_batch, strict=True
                    ):
                        if isinstance(result, BaseException):
                            logger.error(
                                (
                                    'Failed handling of background task (id=%s) '
                                    'for user (service_id=%s).'
                                ),
                                task.id,
                                service_user.id,
                                exc_info=result,
                            )

            offset += limit

            if pagination.count - offset <= 0:
                break

        for task in active_tasks:
            completed_tasks[task.id] = current_datetime

        async with self.bot.storage.transaction() as storage_data:
            storage_data.completed_background_tasks = completed_tasks
