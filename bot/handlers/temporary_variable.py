from telegram.models import Update

from service.models import Connection, TemporaryVariable

from ..context import HandlerContext
from ..storage import Storage
from ..storage.models import UserStorageData
from ..utils.variables import replace_text_variables
from .base import BaseHandler


class TemporaryVariableHandler(BaseHandler[TemporaryVariable]):
    async def handle(
        self, update: Update, variable: TemporaryVariable, context: HandlerContext
    ) -> list[Connection] | None:
        user_storage: Storage[UserStorageData] | None = context.user_storage

        if not user_storage:
            return None

        async with user_storage.transaction() as storage_data:
            storage_data.temporary_variables[
                variable.name
            ] = await replace_text_variables(variable.value, context.variables)

        return variable.source_connections
