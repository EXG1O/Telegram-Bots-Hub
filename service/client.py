from aiohttp import ClientSession, DummyCookieJar, TCPConnector, UnixConnector, hdrs
from aiohttp.typedefs import LooseHeaders
from yarl import URL
import msgspec

from core.msgspec import json_encoder
from core.settings import SERVICE_SOCKET, SERVICE_TOKEN, SERVICE_URL
from core.utils import build_user_agent

from .enums import MessageKeyboardType
from .models import (
    APIRequest,
    BackgroundTask,
    Bot,
    Chat,
    Condition,
    DatabaseOperation,
    DatabaseRecord,
    Invoice,
    Message,
    MessageKeyboardButton,
    Pagination,
    Randomizer,
    TemporaryVariable,
    Timer,
    Trigger,
    User,
    Variable,
)
from .schemas import (
    BindUserToChat,
    CreateChat,
    CreateDatabaseRecord,
    CreateUser,
    UpdateBackgroundTask,
    UpdateBackgroundTasks,
    UpdateDatabaseRecord,
    UpdateDatabaseRecords,
)
from .utils import normalize_params

from collections.abc import Iterable
from typing import Any, overload
import logging

logger = logging.getLogger(__name__)

get_bot_decoder = msgspec.json.Decoder(Bot)
get_triggers_decoder = msgspec.json.Decoder(list[Trigger])
get_trigger_decoder = msgspec.json.Decoder(Trigger)
get_messages_keyboard_buttons_decoder = msgspec.json.Decoder(
    list[MessageKeyboardButton]
)
get_messages_keyboard_button_decoder = msgspec.json.Decoder(MessageKeyboardButton)
get_messages_decoder = msgspec.json.Decoder(list[Message])
get_message_decoder = msgspec.json.Decoder(Message)
get_conditions_decoder = msgspec.json.Decoder(list[Condition])
get_condition_decoder = msgspec.json.Decoder(Condition)
get_background_tasks_decoder = msgspec.json.Decoder(list[BackgroundTask])
update_background_tasks_decoder = msgspec.json.Decoder(list[BackgroundTask])
get_background_task_decoder = msgspec.json.Decoder(BackgroundTask)
update_background_task_decoder = msgspec.json.Decoder(BackgroundTask)
get_api_requests_decoder = msgspec.json.Decoder(list[APIRequest])
get_api_request_decoder = msgspec.json.Decoder(APIRequest)
get_database_operations_decoder = msgspec.json.Decoder(list[DatabaseOperation])
get_database_operation_decoder = msgspec.json.Decoder(DatabaseOperation)
get_invoices_decoder = msgspec.json.Decoder(list[Invoice])
get_invoice_decoder = msgspec.json.Decoder(Invoice)
get_temporary_variables_decoder = msgspec.json.Decoder(list[TemporaryVariable])
get_temporary_variable_decoder = msgspec.json.Decoder(TemporaryVariable)
get_timers_decoder = msgspec.json.Decoder(list[Timer])
get_timer_decoder = msgspec.json.Decoder(Timer)
get_randomizers_decoder = msgspec.json.Decoder(list[Randomizer])
get_randomizer_decoder = msgspec.json.Decoder(Randomizer)
get_variables_decoder = msgspec.json.Decoder(list[Variable])
get_variable_decoder = msgspec.json.Decoder(Variable)
get_chats_decoder = msgspec.json.Decoder(Pagination[Chat])
get_chat_decoder = msgspec.json.Decoder(Chat)
create_chat_decoder = msgspec.json.Decoder(Chat)
get_users_decoder = msgspec.json.Decoder(Pagination[User])
get_user_decoder = msgspec.json.Decoder(User)
create_user_decoder = msgspec.json.Decoder(User)
get_database_records_decoder = msgspec.json.Decoder(list[DatabaseRecord])
update_database_records_decoder = msgspec.json.Decoder(list[DatabaseRecord])
get_database_record_decoder = msgspec.json.Decoder(DatabaseRecord)
create_database_record_decoder = msgspec.json.Decoder(DatabaseRecord)
update_database_record_decoder = msgspec.json.Decoder(DatabaseRecord)


class Client:
    _session: ClientSession | None = None

    def __init__(self, bot_service_id: int) -> None:
        self.url: URL = (
            SERVICE_URL / f'api/telegram-bots-hub/telegram-bots/{bot_service_id}/'
        )
        self.extra_headers: LooseHeaders = {
            hdrs.USER_AGENT: build_user_agent(bot_service_id=bot_service_id)
        }

    @classmethod
    def get_session(cls) -> ClientSession:
        if not cls._session:
            limit: int = 2000
            limit_per_host: int = 0
            keepalive_timeout: int = 60

            cls._session = ClientSession(
                # Don't move the init of the `UnixConnector` class outside of this class, ...
                # because it will cause an error when sending requests.
                connector=UnixConnector(
                    limit=limit,
                    limit_per_host=limit_per_host,
                    keepalive_timeout=keepalive_timeout,
                    path=str(SERVICE_SOCKET),
                )
                if SERVICE_SOCKET
                else TCPConnector(
                    limit=limit,
                    limit_per_host=limit_per_host,
                    keepalive_timeout=keepalive_timeout,
                    ttl_dns_cache=900,
                ),
                headers={
                    hdrs.AUTHORIZATION: f'Token {SERVICE_TOKEN}',
                    hdrs.CONTENT_TYPE: 'application/json',
                },
                cookie_jar=DummyCookieJar(),
                raise_for_status=True,
            )
        return cls._session

    @property
    def session(self) -> ClientSession:
        return self.get_session()

    @overload
    async def _request[T](
        self,
        method: str,
        endpoint: str,
        decoder: msgspec.json.Decoder[T],
        data: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> T: ...

    @overload
    async def _request(
        self,
        method: str,
        endpoint: str,
        decoder: None = None,
        data: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> None: ...

    async def _request[T](
        self,
        method: str,
        endpoint: str,
        decoder: msgspec.json.Decoder[T] | None = None,
        data: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> T | None:
        try:
            async with self.session.request(
                method=method,
                url=self.url / endpoint,
                params=params and normalize_params(params),
                data=data and json_encoder.encode(data),
                headers=self.extra_headers,
            ) as response:
                if not decoder:
                    return None
                body: bytes = await response.read()
            return decoder.decode(body)
        except Exception:
            logger.exception('Failed request to the main service.')
            raise

    async def get_bot(self) -> Bot:
        return await self._request(hdrs.METH_GET, '', decoder=get_bot_decoder)

    async def assign_to_hub(self) -> None:
        await self._request(hdrs.METH_POST, 'hub/assign/')

    async def unassign_from_hub(self) -> None:
        await self._request(hdrs.METH_POST, 'hub/unassign/')

    async def get_triggers(
        self,
        ids: Iterable[int] | None = None,
        command: str | None = None,
        command_payload: str | None = None,
        has_command: bool | None = None,
        has_command_payload: bool | None = None,
        has_command_description: bool | None = None,
        has_message: bool | None = None,
        has_message_text: bool | None = None,
        has_source_connections: bool | None = None,
        has_target_connections: bool | None = None,
    ) -> list[Trigger]:
        return await self._request(
            hdrs.METH_GET,
            'triggers/',
            params={
                'ids': ids,
                'command': command,
                'command_payload': command_payload,
                'has_command': has_command,
                'has_command_payload': has_command_payload,
                'has_command_description': has_command_description,
                'has_message': has_message,
                'has_message_text': has_message_text,
                'has_source_connections': has_source_connections,
                'has_target_connections': has_target_connections,
            },
            decoder=get_triggers_decoder,
        )

    async def get_trigger(self, id: int) -> Trigger:
        return await self._request(
            hdrs.METH_GET, f'triggers/{id}/', decoder=get_trigger_decoder
        )

    async def get_messages_keyboard_buttons(
        self,
        ids: Iterable[int] | None = None,
        type: MessageKeyboardType | None = None,
        text: str | None = None,
    ) -> list[MessageKeyboardButton]:
        return await self._request(
            hdrs.METH_GET,
            'messages-keyboard-buttons/',
            params={'ids': ids, 'type': type, 'text': text},
            decoder=get_messages_keyboard_buttons_decoder,
        )

    async def get_messages_keyboard_button(self, id: int) -> MessageKeyboardButton:
        return await self._request(
            hdrs.METH_GET,
            f'messages-keyboard-buttons/{id}/',
            decoder=get_messages_keyboard_button_decoder,
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

    async def get_background_tasks(
        self, has_source_connections: bool | None = None
    ) -> list[BackgroundTask]:
        return await self._request(
            hdrs.METH_GET,
            'background-tasks/',
            params={'has_source_connections': has_source_connections},
            decoder=get_background_tasks_decoder,
        )

    async def update_background_tasks(
        self,
        data: UpdateBackgroundTasks,
        ids: Iterable[int] | None = None,
    ) -> list[BackgroundTask]:
        return await self._request(
            hdrs.METH_PATCH,
            'background-tasks/update-many/',
            data=data,
            params={'ids': ids},
            decoder=update_background_tasks_decoder,
        )

    async def get_background_task(self, id: int) -> BackgroundTask:
        return await self._request(
            hdrs.METH_GET,
            f'background-tasks/{id}/',
            decoder=get_background_task_decoder,
        )

    async def update_background_task(
        self, id: int, data: UpdateBackgroundTask
    ) -> BackgroundTask:
        return await self._request(
            hdrs.METH_PATCH,
            f'background-tasks/{id}/',
            data=data,
            decoder=update_background_task_decoder,
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

    async def get_temporary_variables(self) -> list[TemporaryVariable]:
        return await self._request(
            hdrs.METH_GET,
            'temporary-variables/',
            decoder=get_temporary_variables_decoder,
        )

    async def get_temporary_variable(self, id: int) -> TemporaryVariable:
        return await self._request(
            hdrs.METH_GET,
            f'temporary-variables/{id}/',
            decoder=get_temporary_variable_decoder,
        )

    async def get_timers(self) -> list[Timer]:
        return await self._request(hdrs.METH_GET, 'timers/', decoder=get_timers_decoder)

    async def get_timer(self, id: int) -> Timer:
        return await self._request(
            hdrs.METH_GET, f'timers/{id}/', decoder=get_timer_decoder
        )

    async def get_randomizers(self) -> list[Randomizer]:
        return await self._request(
            hdrs.METH_GET, 'randomizers/', decoder=get_randomizers_decoder
        )

    async def get_randomizer(self, id: int) -> Randomizer:
        return await self._request(
            hdrs.METH_GET, f'randomizers/{id}/', decoder=get_randomizer_decoder
        )

    async def get_variables(self, name: str | None = None) -> list[Variable]:
        return await self._request(
            hdrs.METH_GET,
            'variables/',
            params={'name': name},
            decoder=get_variables_decoder,
        )

    async def get_variable(self, id: int) -> Variable:
        return await self._request(
            hdrs.METH_GET, f'variables/{id}/', decoder=get_variable_decoder
        )

    async def get_chats(
        self,
        *,
        ids: Iterable[int] | None = None,
        telegram_ids: Iterable[int] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Pagination[Chat]:
        return await self._request(
            hdrs.METH_GET,
            'chats/',
            params={
                'ids': ids,
                'telegram_ids': telegram_ids,
                'limit': limit,
                'offset': offset,
            },
            decoder=get_chats_decoder,
        )

    async def get_chat(self, id: int) -> Chat:
        return await self._request(
            hdrs.METH_GET, f'chats/{id}/', decoder=get_chat_decoder
        )

    async def create_chat(self, data: CreateChat) -> Chat:
        return await self._request(
            hdrs.METH_POST, 'chats/', data=data, decoder=create_chat_decoder
        )

    async def bind_users_to_chat(self, id: int, data: list[BindUserToChat]) -> None:
        return await self._request(hdrs.METH_POST, f'chats/{id}/users/', data=data)

    async def get_users(
        self,
        *,
        ids: Iterable[int] | None = None,
        telegram_ids: Iterable[int] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Pagination[User]:
        return await self._request(
            hdrs.METH_GET,
            'users/',
            params={
                'ids': ids,
                'telegram_ids': telegram_ids,
                'limit': limit,
                'offset': offset,
            },
            decoder=get_users_decoder,
        )

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
        return await self._request(
            hdrs.METH_GET,
            'database-records/',
            params={'search': search, 'has_data_path': has_data_path},
            decoder=get_database_records_decoder,
        )

    async def update_database_records(
        self,
        data: UpdateDatabaseRecords,
        partial: bool = False,
        search: str | None = None,
        has_data_path: str | None = None,
    ) -> list[DatabaseRecord]:
        return await self._request(
            hdrs.METH_PATCH if partial else hdrs.METH_PUT,
            'database-records/update-many/',
            data=data,
            params={'search': search, 'has_data_path': has_data_path},
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
