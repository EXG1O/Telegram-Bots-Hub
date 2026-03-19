from telegram.models import Update

from service.models import Connection, TemporaryVariable

from ..context import HandlerContext
from ..storage import Storage
from ..utils.variables import replace_text_variables
from .base import BaseHandler

from typing import Any


class TemporaryVariableHandler(BaseHandler[TemporaryVariable]):
    async def handle(
        self, update: Update, variable: TemporaryVariable, context: HandlerContext
    ) -> list[Connection] | None:
        user_storage: Storage | None = context.user_storage

        if not user_storage:
            return None

        variables: dict[str, Any] = await user_storage.get('temporary_variables', {})
        variables[variable.name] = await replace_text_variables(
            variable.value, context.variables
        )
        await user_storage.set('temporary_variables', variables)

        return variable.source_connections
