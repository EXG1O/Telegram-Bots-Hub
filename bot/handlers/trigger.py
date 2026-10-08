from telegram import Update, User

from service import Trigger

from ..context import Context
from ..storage import Subscriber, SubscriptionType
from .base import BaseHandler


class TriggerHandler(BaseHandler[Trigger]):
    async def handle(self, update: Update, trigger: Trigger, context: Context) -> None:
        if (chat := update.effective_chat) and trigger.webhook is not None:
            user: User | None = update.effective_user
            async with self._bot.storage.transaction() as storage_data:
                storage_data.subscribers[SubscriptionType.TRIGGER].setdefault(
                    trigger.id, set()
                ).add(Subscriber(chat_id=chat.id, user_id=user.id if user else None))
            return

        if user_storage := context.user_storage:
            async with user_storage.transaction() as storage_data:
                storage_data.subscriptions[SubscriptionType.TRIGGER].add(trigger.id)
            return
