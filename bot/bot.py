from telegram.client import TelegramClient
from telegram.enums import ChatType, UpdateType
from telegram.exceptions import TelegramError
from telegram.models import BotCommand, Chat, Update, User

from multidict import MultiDict
import msgspec

from core.enums import Mode
from core.msgspec import json_decoder
from core.settings import MODE, TELEGRAM_TOKEN
from core.storage import bots
from service.client import ServiceClient
from service.enums import ChatType as ServiceChatType
from service.models import Bot as ServiceBot
from service.models import Chat as ServiceChat
from service.models import Pagination, Trigger
from service.models import User as ServiceUser
from service.schemas import BindUserToChat, CreateChat, CreateUser

from .background.manager import BackgroundTaskManager
from .context import HandlerContext
from .exceptions import NoTriggerSubscribersError
from .handler import Handler
from .storage import Storage
from .storage.models import TriggerSubscriber
from .utils.validation import are_subjects_allowed, is_subject_allowed

from collections.abc import Awaitable, Iterable
from contextlib import suppress
from itertools import batched, repeat
from typing import TYPE_CHECKING, Any, Final
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

        return are_subjects_allowed(
            service_bot=service_bot,
            service_chat=service_chat,
            service_user=service_user,
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

    async def _handle_webhook_trigger(
        self,
        service_chat: ServiceChat,
        service_user: ServiceUser | None,
        trigger: Trigger,
        payload: Any,
    ) -> None:
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

        if service_user:
            update._effective_user = User(
                id=service_user.telegram_id,
                username=service_user.username,
                first_name=service_user.first_name,
                last_name=service_user.last_name,
                is_bot=service_user.is_bot,
                is_premium=service_user.is_premium,
            )

        context = HandlerContext(self, update)
        context.variables.store['WEBHOOK_PAYLOAD'] = payload

        await self.handler.connection_handler.handle_many(
            update, trigger.source_connections, context
        )

    async def _get_webhook_trigger_allowed_subjects(
        self,
        service_bot: ServiceBot,
        trigger: Trigger,
        trigger_has_target_connections: bool,
        limit: int,
        offset: int,
    ) -> tuple[Iterable[ServiceChat], Iterable[ServiceUser | None], bool]:
        if not trigger_has_target_connections:
            pagination: Pagination[ServiceChat] = await self.service.get_chats(
                limit=limit, offset=offset
            )
            return (
                filter(
                    lambda chat: is_subject_allowed(
                        service_bot=service_bot, service_subject=chat
                    ),
                    pagination.results,
                ),
                repeat(None, len(pagination.results)),
                pagination.count - (offset + limit) <= 0,
            )

        async with self.storage.transaction() as storage_data:
            raw_subscribers: set[TriggerSubscriber] | None = (
                storage_data.expected_triggers.pop(trigger.id, None)
            )

            if not raw_subscribers:
                raise NoTriggerSubscribersError(trigger.id)

            subscribers: list[TriggerSubscriber] = list(raw_subscribers)
            subscriber_batch: list[TriggerSubscriber] = subscribers[:limit]
            subscribers = subscribers[limit:]

            if subscribers:
                storage_data.expected_triggers[trigger.id] = set(subscribers)

        chat_id_user_id_pair: MultiDict[int | None] = MultiDict(
            [
                (str(subscriber.chat_id), subscriber.user_id)
                for subscriber in subscriber_batch
            ]
        )

        service_chat_pagination, service_user_pagination = await asyncio.gather(
            self.service.get_chats(
                telegram_ids=map(int, chat_id_user_id_pair.keys()),
                limit=limit,
                offset=offset,
            ),
            self.service.get_users(
                telegram_ids=filter(None, chat_id_user_id_pair.values()),
                limit=limit,
                offset=offset,
            ),
        )
        service_chats: dict[int, ServiceChat] = {
            chat.telegram_id: chat for chat in service_chat_pagination.results
        }
        service_users: dict[int, ServiceUser] = {
            user.telegram_id: user for user in service_user_pagination.results
        }

        result_service_chats: list[ServiceChat] = []
        result_service_users: list[ServiceUser | None] = []

        for chat_id, user_id in chat_id_user_id_pair.items():
            service_chat: ServiceChat | None = service_chats.get(int(chat_id))
            service_user: ServiceUser | None = (
                service_users.get(user_id) if user_id else None
            )

            if not (
                service_chat
                and are_subjects_allowed(
                    service_bot=service_bot,
                    service_chat=service_chat,
                    service_user=service_user,
                )
            ):
                continue

            result_service_chats.append(service_chat)
            result_service_users.append(service_user)

        return (
            result_service_chats,
            result_service_users,
            service_chat_pagination.count - (offset + limit) <= 0,
        )

    async def feed_webhook_trigger(
        self, trigger: Trigger, trigger_has_target_connections: bool, payload: str
    ) -> None:
        if not trigger.source_connections:
            return

        service_bot: ServiceBot = await self.service.get_bot()

        if TYPE_CHECKING:
            processed_payload: Any | str

        try:
            processed_payload = json_decoder.decode(payload)
        except msgspec.DecodeError:
            processed_payload = payload

        limit: int = 250
        offset: int = 0
        batch_size: int = 15

        while True:
            try:
                (
                    service_chats,
                    service_users,
                    is_pagination_complete,
                ) = await self._get_webhook_trigger_allowed_subjects(
                    service_bot, trigger, trigger_has_target_connections, limit, offset
                )
            except NoTriggerSubscribersError:
                logger.debug(
                    'Webhook trigger (service_id=%s) has no subscribers.', trigger.id
                )
                break

            for service_chat_batch, service_user_batch in zip(
                batched(service_chats, batch_size, strict=False),
                batched(service_users, batch_size, strict=False),
                strict=True,
            ):
                results: list[BaseException | None] = await asyncio.gather(
                    *[
                        self._handle_webhook_trigger(
                            service_chat, service_user, trigger, processed_payload
                        )
                        for service_chat, service_user in zip(
                            service_chat_batch, service_user_batch, strict=True
                        )
                    ],
                    return_exceptions=True,
                )

            if MODE == Mode.DEBUG:
                for result, service_chat, service_user in zip(
                    results, service_chat_batch, service_user_batch, strict=True
                ):
                    if isinstance(result, BaseException):
                        logger.error(
                            'Failed processing webhook trigger (service_id=%s) '
                            'for chat (service_id=%s), user (service_id=%s).',
                            trigger.id,
                            service_chat.id,
                            service_user and service_user.id,
                            exc_info=result,
                        )

            if is_pagination_complete:
                break

            offset += limit

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
