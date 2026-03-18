from telegram.enums import ChatType
from telegram.exceptions import InvalidTokenError
from telegram.models import Chat, Update, User

from service.models import BackgroundTask
from service.models import Bot as ServiceBot
from service.models import User as ServiceUser

from .context import HandlerContext
from .utils.validation import is_valid_user

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
            current_datetime: datetime = datetime.now(UTC)
            storage_tasks: dict[str, str] = await self.bot.storage.get(
                'background_tasks', {}
            )

            for task in tasks:
                try:
                    if (
                        datetime.fromisoformat(
                            storage_tasks.setdefault(
                                str(task.id), datetime.isoformat(current_datetime)
                            )
                        )
                        + timedelta(days=task.interval.value)
                    ) > current_datetime:
                        continue

                    if service_users is None:
                        service_users = await self.bot.service.get_users()

                    if not service_users:
                        break

                    if service_bot is None:
                        service_bot = await self.bot.service.get_bot()

                    await asyncio.gather(
                        *[
                            self._handle_background_task(
                                service_bot, service_user, task
                            )
                            for service_user in service_users
                        ]
                    )

                    storage_tasks[str(task.id)] = datetime.isoformat(current_datetime)
                except Exception:
                    pass  # FIXME: In the future, error logging will be added here.

            await self.bot.storage.set('background_tasks', storage_tasks)

    async def start(self) -> None:
        self.tasks.add(asyncio.create_task(self._monitor_token()))
        self.tasks.add(asyncio.create_task(self._process_background_tasks()))

    async def stop(self) -> None:
        for task in self.tasks:
            task.cancel()
