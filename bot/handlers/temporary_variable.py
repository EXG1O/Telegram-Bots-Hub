from telegram.models import Update

from service.models import Connection, TemporaryVariable

from ..context import HandlerContext
from ..utils.variables import replace_text_variables
from .base import BaseHandler

from typing import Any


class TemporaryVariableHandler(BaseHandler[TemporaryVariable]):
    async def handle(
        self, update: Update, variable: TemporaryVariable, context: HandlerContext
    ) -> list[Connection]:
        temporary: dict[str, Any] = context.variables.store.setdefault('TEMPORARY', {})
        temporary[variable.name] = await replace_text_variables(
            variable.value, context.variables
        )
        return variable.source_connections
