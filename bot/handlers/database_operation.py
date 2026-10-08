from telegram import Update

from service import (
    Connection,
    CreateDatabaseRecord,
    DatabaseCreateOperation,
    DatabaseOperation,
    DatabaseRecord,
    DatabaseUpdateOperation,
    UpdateDatabaseRecords,
)

from ..context import Context
from ..utils.variables import replace_data_variables, replace_text_variables
from .base import BaseHandler

import asyncio
import json


class DatabaseOperationHandler(BaseHandler[DatabaseOperation]):
    async def handle(
        self,
        update: Update,
        database_operation: DatabaseOperation,
        context: Context,
    ) -> list[Connection] | None:
        create_operation: DatabaseCreateOperation | None = (
            database_operation.create_operation
        )
        update_operation: DatabaseUpdateOperation | None = (
            database_operation.update_operation
        )

        if create_operation:
            await self._bot.service.create_database_record(
                CreateDatabaseRecord(
                    data=await replace_data_variables(
                        create_operation.data, context.variables, deserialize=True
                    )
                )
            )
        elif update_operation:
            data, lookup_field_value = await asyncio.gather(
                replace_data_variables(
                    update_operation.new_data, context.variables, deserialize=True
                ),
                replace_text_variables(
                    update_operation.lookup_field_value,
                    context.variables,
                    deserialize=True,
                ),
            )

            records: list[
                DatabaseRecord
            ] = await self._bot.service.update_database_records(
                UpdateDatabaseRecords(data=data),
                partial=not update_operation.overwrite,
                search=(
                    f'"{update_operation.lookup_field_name}": '
                    + json.dumps(lookup_field_value)
                ),
            )

            if not records and update_operation.create_if_not_found:
                await self._bot.service.create_database_record(
                    CreateDatabaseRecord(data=data)
                )
        else:
            return None

        return database_operation.source_connections
