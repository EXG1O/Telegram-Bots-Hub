from telegram.models import Chat, Update, User

from service.models import Trigger

from ..context import HandlerContext
from ..storage import Storage
from ..storage.models import TriggerSubscriber, UserStorageData
from .base import BaseHandler


class TriggerHandler(BaseHandler[Trigger]):
    async def handle(
        self, update: Update, trigger: Trigger, context: HandlerContext
    ) -> None:
        chat: Chat | None = update.effective_chat
        user: User | None = update.effective_user

        if chat and trigger.webhook is not None:
            async with self.bot.storage.transaction() as storage_data:
                storage_data.expected_triggers.setdefault(trigger.id, set()).add(
                    TriggerSubscriber(
                        chat_id=chat.id, user_id=user.id if user else None
                    )
                )
            return

        user_storage: Storage[UserStorageData] | None = context.user_storage

        if not user_storage:
            return

        async with user_storage.transaction() as storage_data:
            storage_data.expected_trigger_id = trigger.id
