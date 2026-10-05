from telegram import Chat, ChatType, Update

from core.enums import Mode
from core.settings import MODE
import service

from ...context import HandlerContext
from ...storage.models import BotStorageData
from ...utils.validation import is_service_subject_allowed
from .base import BackgroundTask

from datetime import UTC, datetime, timedelta
from itertools import batched
import asyncio
import logging

logger = logging.getLogger(__name__)


class ProcessServiceTasksTask(BackgroundTask):
    async def _handle_task(
        self,
        service_bot: service.Bot,
        service_chat: service.Chat,
        task: service.BackgroundTask,
    ) -> None:
        if not is_service_subject_allowed(bot=service_bot, subject=service_chat):
            return

        update = Update(update_id=0)
        update._effective_chat = Chat(
            id=service_chat.telegram_id,
            type=ChatType(service_chat.type),
            title=service_chat.title,
            username=service_chat.username,
            first_name=service_chat.first_name,
            last_name=service_chat.last_name,
            is_forum=service_chat.is_forum,
            is_direct_messages=service_chat.is_direct_messages,
        )

        await self.bot.handler.connection_handler.handle_many(
            update, task.source_connections, HandlerContext(self.bot, update)
        )

    def _should_skip_task(
        self,
        task: service.BackgroundTask,
        last_completed_tasks: dict[int, datetime],
        current_datetime: datetime,
    ) -> tuple[bool, datetime]:
        last_completed_task_datetime: datetime | None = last_completed_tasks.get(
            task.id
        )

        if last_completed_task_datetime is None:
            return True, current_datetime

        if (
            last_completed_task_datetime
            + timedelta(seconds=1 if MODE == Mode.DEBUG else task.interval)
            > current_datetime
        ):
            return True, last_completed_task_datetime

        return False, current_datetime

    async def __call__(self) -> None:
        tasks: list[
            service.BackgroundTask
        ] = await self.bot.service.get_background_tasks(has_source_connections=True)

        if not tasks:
            return

        storage_data: BotStorageData = await self.bot.storage.get_data()
        last_completed_tasks: dict[int, datetime] = (
            storage_data.completed_background_tasks
        )

        active_tasks: list[service.BackgroundTask] = []
        active_task_ids: set[int] = set()
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
                active_task_ids.add(task.id)

        if not active_tasks:
            async with self.bot.storage.transaction() as storage_data:
                storage_data.completed_background_tasks.update(completed_tasks)
            return

        service_bot, *_ = await asyncio.gather(
            self.bot.service.get_bot(),
            self.bot.service.update_background_tasks(
                ids=active_task_ids,
                data=service.UpdateBackgroundTasks(
                    status=service.BackgroundTaskStatus.RUNNING
                ),
            ),
        )

        limit: int = 150
        offset: int = 0
        batch_size: int = 15

        try:
            while True:
                pagination: service.Pagination[
                    service.Chat
                ] = await self.bot.service.get_chats(limit=limit, offset=offset)
                service_chats: list[service.Chat] = pagination.results

                if not service_chats:
                    break

                for task in active_tasks:
                    for service_chat_batch in batched(
                        service_chats, batch_size, strict=False
                    ):
                        results: list[BaseException | None] = await asyncio.gather(
                            *[
                                self._handle_task(service_bot, service_chat, task)
                                for service_chat in service_chat_batch
                            ],
                            return_exceptions=True,
                        )

                    if MODE == Mode.DEBUG:
                        for result, service_chat in zip(
                            results, service_chat_batch, strict=True
                        ):
                            if isinstance(result, BaseException):
                                logger.error(
                                    (
                                        'Failed handling of background task (service_id=%d) '
                                        'for chat (service_id=%d).'
                                    ),
                                    task.id,
                                    service_chat.id,
                                    exc_info=result,
                                )

                offset += limit

                if pagination.count - offset <= 0:
                    break

            for task in active_tasks:
                completed_tasks[task.id] = current_datetime

            async with self.bot.storage.transaction() as storage_data:
                storage_data.completed_background_tasks = completed_tasks
        finally:
            await self.bot.service.update_background_tasks(
                ids=active_task_ids,
                data=service.UpdateBackgroundTasks(
                    status=service.BackgroundTaskStatus.PENDING
                ),
            )
