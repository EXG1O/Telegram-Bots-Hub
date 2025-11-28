from telegram import Update

from service.models import (
    Connection,
    DatabaseCreateOperation,
    DatabaseOperation,
    DatabaseRecord,
    DatabaseUpdateOperation,
)
from service.schemas import CreateDatabaseRecord, UpdateDatabaseRecords

from ..storage import EventStorage
from ..utils import replace_data_variables, replace_text_variables
from ..variables import Variables
from .base import BaseHandler

import asyncio
import json


class DatabaseOperationHandler(BaseHandler[DatabaseOperation]):
    async def handle(
        self,
        update: Update,
        database_operation: DatabaseOperation,
        event_storage: EventStorage,
        variables: Variables,
    ) -> list[Connection] | None:
        create_operation: DatabaseCreateOperation | None = (
            database_operation.create_operation
        )
        update_operation: DatabaseUpdateOperation | None = (
            database_operation.update_operation
        )

        if create_operation:
            await self.bot.service_api.create_database_record(
                CreateDatabaseRecord(
                    data=await replace_data_variables(
                        create_operation.data, variables, deserialize=True
                    )
                )
            )
        elif update_operation:
            data, lookup_field_value = await asyncio.gather(
                replace_data_variables(
                    update_operation.new_data, variables, deserialize=True
                ),
                replace_text_variables(
                    update_operation.lookup_field_value,
                    variables,
                    deserialize=True,
                ),
            )

            records: list[
                DatabaseRecord
            ] = await self.bot.service_api.update_database_records(
                UpdateDatabaseRecords(data=data),
                partial=not update_operation.overwrite,
                search=(
                    f'"{update_operation.lookup_field_name}": '
                    + json.dumps(lookup_field_value)
                ),
            )

            if not records and update_operation.create_if_not_found:
                await self.bot.service_api.create_database_record(
                    CreateDatabaseRecord(data=data)
                )
        else:
            return None

        return database_operation.source_connections
