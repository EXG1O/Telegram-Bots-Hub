from telegram import Update

from service.models import Trigger

from ..storage import EventStorage
from ..variables import Variables
from .base import BaseHandler


class TriggerHandler(BaseHandler[Trigger]):
    async def handle(
        self,
        update: Update,
        trigger: Trigger,
        event_storage: EventStorage,
        variables: Variables,
    ) -> None:
        if not event_storage.user:
            return

        await event_storage.user.set('expected_trigger_id', trigger.id)
