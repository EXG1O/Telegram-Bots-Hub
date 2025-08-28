from telegram import Update

from service.models import (
    Connection,
    DatabaseCreateOperation,
    DatabaseOperation,
    DatabaseRecord,
    DatabaseUpdateOperation,
)
from service.schemas import CreateDatabaseRecord, UpdateDatabaseRecords

from ..utils import replace_text_variables
from ..variables import Variables
from .base import BaseHandler

from typing import Any
import json


class DatabaseOperationHandler(BaseHandler[DatabaseOperation]):
    async def _create_record(self, data: Any, variables: Variables) -> DatabaseRecord:
        return await self.bot.service_api.create_database_record(
            CreateDatabaseRecord(
                data=json.loads(
                    await replace_text_variables(json.dumps(data), variables)
                )
            )
        )

    async def handle(
        self,
        update: Update,
        database_operation: DatabaseOperation,
        variables: Variables,
    ) -> list[Connection] | None:
        create_operation: DatabaseCreateOperation | None = (
            database_operation.create_operation
        )
        update_operation: DatabaseUpdateOperation | None = (
            database_operation.update_operation
        )

        if create_operation:
            await self._create_record(create_operation.data, variables)
        elif update_operation:
            await self.bot.service_api.update_database_records(
                UpdateDatabaseRecords(
                    data=json.loads(
                        await replace_text_variables(
                            json.dumps(update_operation.new_data), variables
                        )
                    )
                ),
                partial=not update_operation.overwrite,
                search=(
                    f'"{update_operation.lookup_field_name}": '
                    + json.dumps(update_operation.lookup_field_value)
                ),
            )
        else:
            return None

        return database_operation.source_connections
