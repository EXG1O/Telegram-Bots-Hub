from telegram.models import Update

from service.models import Trigger

from ..context import HandlerContext
from ..storage import Storage
from .base import BaseHandler


class TriggerHandler(BaseHandler[Trigger]):
    async def handle(
        self, update: Update, trigger: Trigger, context: HandlerContext
    ) -> None:
        user_storage: Storage | None = context.user_storage

        if not user_storage:
            return

        await user_storage.set('expected_trigger_id', trigger.id)
