from aiohttp import ClientSession, DummyCookieJar, UnixConnector, hdrs
from aiohttp.typedefs import LooseHeaders
from yarl import URL
import msgspec

from core.msgspec import json_encoder
from core.settings import SERVICE_TOKEN, SERVICE_UNIX_SOCK, SERVICE_URL

from .models import (
    APIRequest,
    BackgroundTask,
    Bot,
    Condition,
    DatabaseOperation,
    DatabaseRecord,
    Invoice,
    Message,
    MessageKeyboardButton,
    Trigger,
    User,
    Variable,
)
from .schemas import (
    CreateDatabaseRecord,
    CreateUser,
    UpdateDatabaseRecord,
    UpdateDatabaseRecords,
)

from typing import Any, Final

HEADERS: Final[LooseHeaders] = {
    hdrs.AUTHORIZATION: f'Token {SERVICE_TOKEN}',
    hdrs.CONTENT_TYPE: 'application/json',
}


get_bot_decoder = msgspec.json.Decoder(Bot)
get_triggers_decoder = msgspec.json.Decoder(list[Trigger])
get_trigger_decoder = msgspec.json.Decoder(Trigger)
get_messages_keyboard_buttons_decoder = msgspec.json.Decoder(
    list[MessageKeyboardButton]
)
get_messages_decoder = msgspec.json.Decoder(list[Message])
get_message_decoder = msgspec.json.Decoder(Message)
get_conditions_decoder = msgspec.json.Decoder(list[Condition])
get_condition_decoder = msgspec.json.Decoder(Condition)
get_background_tasks_decoder = msgspec.json.Decoder(list[BackgroundTask])
get_background_task_decoder = msgspec.json.Decoder(BackgroundTask)
get_api_requests_decoder = msgspec.json.Decoder(list[APIRequest])
get_api_request_decoder = msgspec.json.Decoder(APIRequest)
get_database_operations_decoder = msgspec.json.Decoder(list[DatabaseOperation])
get_database_operation_decoder = msgspec.json.Decoder(DatabaseOperation)
get_invoices_decoder = msgspec.json.Decoder(list[Invoice])
get_invoice_decoder = msgspec.json.Decoder(Invoice)
get_variables_decoder = msgspec.json.Decoder(list[Variable])
get_variable_decoder = msgspec.json.Decoder(Variable)
get_users_decoder = msgspec.json.Decoder(list[User])
get_user_decoder = msgspec.json.Decoder(User)
create_user_decoder = msgspec.json.Decoder(User)
get_database_records_decoder = msgspec.json.Decoder(list[DatabaseRecord])
update_database_records_decoder = msgspec.json.Decoder(list[DatabaseRecord])
get_database_record_decoder = msgspec.json.Decoder(DatabaseRecord)
create_database_record_decoder = msgspec.json.Decoder(DatabaseRecord)
update_database_record_decoder = msgspec.json.Decoder(DatabaseRecord)


class ServiceClient:
    _session: ClientSession | None = None

    def __init__(self, bot_service_id: int) -> None:
        self.root_url: URL = (
            SERVICE_URL / f'api/telegram-bots-hub/telegram-bots/{bot_service_id}/'
        )

    @classmethod
    def get_session(cls) -> ClientSession:
        if not cls._session:
            cls._session = ClientSession(
                # Don't move the init of the `UnixConnector` class outside of this class, ...
                # because it will cause an error when sending requests.
                connector=UnixConnector(path=str(SERVICE_UNIX_SOCK))
                if SERVICE_UNIX_SOCK
                else None,
                headers=HEADERS,
                cookie_jar=DummyCookieJar(),
                raise_for_status=True,
            )
        return cls._session

    @property
    def session(self) -> ClientSession:
        return self.get_session()

    async def _request[T](
        self,
        method: str,
        endpoint: str,
        decoder: msgspec.json.Decoder[T],
        data: Any | None = None,
        params: dict[str, str] | None = None,
    ) -> T:
        async with self.session.request(
            method=method,
            url=self.root_url / endpoint,
            data=data and json_encoder.encode(data),
            params=params,
        ) as response:
            body: bytes = await response.read()
        return decoder.decode(body)

    async def get_bot(self) -> Bot:
        return await self._request(hdrs.METH_GET, '', decoder=get_bot_decoder)

    async def get_triggers(
        self,
        command: str | None = None,
        command_payload: str | None = None,
        has_command: bool | None = None,
        has_command_payload: bool | None = None,
        has_command_description: bool | None = None,
        has_message: bool | None = None,
        has_message_text: bool | None = None,
        has_target_connections: bool | None = None,
    ) -> list[Trigger]:
        params: dict[str, str] = {}

        if command is not None:
            params['command'] = command
        if command_payload is not None:
            params['command_payload'] = command_payload
        if has_command is not None:
            params['has_command'] = str(has_command)
        if has_command_payload is not None:
            params['has_command_payload'] = str(has_command_payload)
        if has_command_description is not None:
            params['has_command_description'] = str(has_command_description)
        if has_message is not None:
            params['has_message'] = str(has_message)
        if has_message_text is not None:
            params['has_message_text'] = str(has_message_text)
        if has_target_connections is not None:
            params['has_target_connections'] = str(has_target_connections)

        return await self._request(
            hdrs.METH_GET, 'triggers/', params=params, decoder=get_triggers_decoder
        )

    async def get_trigger(self, id: int) -> Trigger:
        return await self._request(
            hdrs.METH_GET, f'triggers/{id}/', decoder=get_trigger_decoder
        )

    async def get_messages_keyboard_buttons(
        self, id: int | None = None, text: str | None = None
    ) -> list[MessageKeyboardButton]:
        params: dict[str, str] = {}

        if id is not None:
            params['id'] = str(id)
        if text is not None:
            params['text'] = text

        return await self._request(
            hdrs.METH_GET,
            'messages-keyboard-buttons/',
            params=params,
            decoder=get_messages_keyboard_buttons_decoder,
        )

    async def get_messages(self) -> list[Message]:
        return await self._request(
            hdrs.METH_GET, 'messages/', decoder=get_messages_decoder
        )

    async def get_message(self, id: int) -> Message:
        return await self._request(
            hdrs.METH_GET, f'messages/{id}/', decoder=get_message_decoder
        )

    async def get_conditions(self) -> list[Condition]:
        return await self._request(
            hdrs.METH_GET, 'conditions/', decoder=get_conditions_decoder
        )

    async def get_condition(self, id: int) -> Condition:
        return await self._request(
            hdrs.METH_GET, f'conditions/{id}/', decoder=get_condition_decoder
        )

    async def get_background_tasks(self) -> list[BackgroundTask]:
        return await self._request(
            hdrs.METH_GET, 'background-tasks/', decoder=get_background_tasks_decoder
        )

    async def get_background_task(self, id: int) -> BackgroundTask:
        return await self._request(
            hdrs.METH_GET,
            f'background-tasks/{id}/',
            decoder=get_background_task_decoder,
        )

    async def get_api_requests(self) -> list[APIRequest]:
        return await self._request(
            hdrs.METH_GET, 'api-requests/', decoder=get_api_requests_decoder
        )

    async def get_api_request(self, id: int) -> APIRequest:
        return await self._request(
            hdrs.METH_GET, f'api-requests/{id}/', decoder=get_api_request_decoder
        )

    async def get_database_operations(self) -> list[DatabaseOperation]:
        return await self._request(
            hdrs.METH_GET,
            'database-operations/',
            decoder=get_database_operations_decoder,
        )

    async def get_database_operation(self, id: int) -> DatabaseOperation:
        return await self._request(
            hdrs.METH_GET,
            f'database-operations/{id}/',
            decoder=get_database_operation_decoder,
        )

    async def get_invoices(self) -> list[Invoice]:
        return await self._request(
            hdrs.METH_GET, 'invoices/', decoder=get_invoices_decoder
        )

    async def get_invoice(self, id: int) -> Invoice:
        return await self._request(
            hdrs.METH_GET, f'invoices/{id}/', decoder=get_invoice_decoder
        )

    async def get_variables(self, name: str | None = None) -> list[Variable]:
        params: dict[str, str] = {}

        if name is not None:
            params['name'] = name

        return await self._request(
            hdrs.METH_GET, 'variables/', decoder=get_variables_decoder
        )

    async def get_variable(self, id: int) -> Variable:
        return await self._request(
            hdrs.METH_GET, f'variables/{id}/', decoder=get_variable_decoder
        )

    async def get_users(self) -> list[User]:
        return await self._request(hdrs.METH_GET, 'users/', decoder=get_users_decoder)

    async def get_user(self, id: int) -> User:
        return await self._request(
            hdrs.METH_GET, f'users/{id}/', decoder=get_user_decoder
        )

    async def create_user(self, data: CreateUser) -> User:
        return await self._request(
            hdrs.METH_POST, 'users/', data=data, decoder=create_user_decoder
        )

    async def get_database_records(
        self, search: str | None = None, has_data_path: str | None = None
    ) -> list[DatabaseRecord]:
        params: dict[str, str] = {}

        if search is not None:
            params['search'] = search
        if has_data_path is not None:
            params['has_data_path'] = has_data_path

        return await self._request(
            hdrs.METH_GET,
            'database-records/',
            params=params,
            decoder=get_database_records_decoder,
        )

    async def update_database_records(
        self,
        data: UpdateDatabaseRecords,
        partial: bool = False,
        search: str | None = None,
        has_data_path: str | None = None,
    ) -> list[DatabaseRecord]:
        params: dict[str, str] = {}

        if search is not None:
            params['search'] = search
        if has_data_path is not None:
            params['has_data_path'] = has_data_path

        return await self._request(
            hdrs.METH_PATCH if partial else hdrs.METH_PUT,
            'database-records/update-many/',
            data=data,
            params=params,
            decoder=update_database_records_decoder,
        )

    async def get_database_record(self, id: int) -> DatabaseRecord:
        return await self._request(
            hdrs.METH_GET,
            f'database-records/{id}/',
            decoder=get_database_record_decoder,
        )

    async def create_database_record(
        self, data: CreateDatabaseRecord
    ) -> DatabaseRecord:
        return await self._request(
            hdrs.METH_POST,
            'database-records/',
            data=data,
            decoder=create_database_record_decoder,
        )

    async def update_database_record(
        self, id: int, data: UpdateDatabaseRecord
    ) -> DatabaseRecord:
        return await self._request(
            hdrs.METH_PUT,
            f'database-records/{id}/',
            data=data,
            decoder=update_database_record_decoder,
        )
