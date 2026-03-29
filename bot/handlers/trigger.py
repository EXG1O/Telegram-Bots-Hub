from telegram.models import Update

from service.models import Trigger

from ..context import HandlerContext
from ..storage import Storage
from ..storage.models import UserStorageData
from .base import BaseHandler


class TriggerHandler(BaseHandler[Trigger]):
    async def handle(
        self, update: Update, trigger: Trigger, context: HandlerContext
    ) -> None:
        user_storage: Storage[UserStorageData] | None = context.user_storage

        if not user_storage:
            return

        async with user_storage.transaction() as storage_data:
            storage_data.expected_trigger_id = trigger.id
