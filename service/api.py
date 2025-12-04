from aiohttp import ClientSession, UnixConnector
from aiohttp.hdrs import METH_PATCH, METH_PUT
from aiohttp.typedefs import LooseHeaders
from dacite import Config, from_dict
from yarl import URL

from core.settings import SERVICE_TOKEN, SERVICE_UNIX_SOCK, SERVICE_URL

from .enums import (
    APIRequestMethod,
    BackgroundTaskInterval,
    ConditionPartNextPartOperator,
    ConditionPartOperator,
    ConditionPartType,
    ConnectionSourceObjectType,
    ConnectionTargetObjectType,
    MessageKeyboardType,
)
from .models import (
    APIRequest,
    BackgroundTask,
    Bot,
    Condition,
    DatabaseOperation,
    DatabaseRecord,
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

from typing import Final

config = Config(
    type_hooks={
        cls: cls
        for cls in [
            ConnectionSourceObjectType,
            ConnectionTargetObjectType,
            APIRequestMethod,
            MessageKeyboardType,
            ConditionPartType,
            ConditionPartOperator,
            ConditionPartNextPartOperator,
            BackgroundTaskInterval,
        ]
    }
)

HEADERS: Final[LooseHeaders] = {'Authorization': f'Token {SERVICE_TOKEN}'}


class API:
    """Bot API for getting data from the main service."""

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
                raise_for_status=True,
            )
        return cls._session

    @property
    def session(self) -> ClientSession:
        return self.get_session()

    async def get_bot(self) -> Bot:
        async with self.session.get(self.root_url) as response:
            return from_dict(Bot, await response.json(), config)

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

        async with self.session.get(
            self.root_url / 'triggers/', params=params
        ) as response:
            return [from_dict(Trigger, data, config) for data in await response.json()]

    async def get_trigger(self, id: int) -> Trigger:
        async with self.session.get(self.root_url / f'triggers/{id}/') as response:
            return from_dict(Trigger, await response.json(), config)

    async def get_messages_keyboard_buttons(
        self, id: int | None = None, text: str | None = None
    ) -> list[MessageKeyboardButton]:
        params: dict[str, str] = {}

        if id is not None:
            params['id'] = str(id)
        if text is not None:
            params['text'] = text

        async with self.session.get(
            self.root_url / 'messages-keyboard-buttons/', params=params
        ) as response:
            return [
                from_dict(MessageKeyboardButton, data, config)
                for data in await response.json()
            ]

    async def get_messages(self) -> list[Message]:
        async with self.session.get(self.root_url / 'messages/') as response:
            return [from_dict(Message, data, config) for data in await response.json()]

    async def get_message(self, id: int) -> Message:
        async with self.session.get(self.root_url / f'messages/{id}/') as response:
            return from_dict(Message, await response.json(), config)

    async def get_conditions(self) -> list[Condition]:
        async with self.session.get(self.root_url / 'conditions/') as response:
            return [
                from_dict(Condition, data, config) for data in await response.json()
            ]

    async def get_condition(self, id: int) -> Condition:
        async with self.session.get(self.root_url / f'conditions/{id}/') as response:
            return from_dict(Condition, await response.json(), config)

    async def get_background_tasks(self) -> list[BackgroundTask]:
        async with self.session.get(self.root_url / 'background-tasks/') as response:
            return [
                from_dict(BackgroundTask, data, config)
                for data in await response.json()
            ]

    async def get_background_task(self, id: int) -> BackgroundTask:
        async with self.session.get(f'background-tasks/{id}/') as response:
            return from_dict(BackgroundTask, await response.json(), config)

    async def get_api_requests(self) -> list[APIRequest]:
        async with self.session.get(self.root_url / 'api-requests/') as response:
            return [
                from_dict(APIRequest, data, config) for data in await response.json()
            ]

    async def get_api_request(self, id: int) -> APIRequest:
        async with self.session.get(self.root_url / f'api-requests/{id}/') as response:
            return from_dict(APIRequest, await response.json(), config)

    async def get_database_operations(self) -> list[DatabaseOperation]:
        async with self.session.get(self.root_url / 'database-operations/') as response:
            return [
                from_dict(DatabaseOperation, data, config)
                for data in await response.json()
            ]

    async def get_database_operation(self, id: int) -> DatabaseOperation:
        async with self.session.get(
            self.root_url / f'database-operations/{id}/'
        ) as response:
            return from_dict(DatabaseOperation, await response.json(), config)

    async def get_variables(self, name: str | None = None) -> list[Variable]:
        params: dict[str, str] = {}

        if name is not None:
            params['name'] = name

        async with self.session.get(
            self.root_url / 'variables/', params=params
        ) as response:
            return [from_dict(Variable, data, config) for data in await response.json()]

    async def get_variable(self, id: int) -> Variable:
        async with self.session.get(self.root_url / f'variables/{id}/') as response:
            return from_dict(Variable, await response.json(), config)

    async def get_users(self) -> list[User]:
        async with self.session.get(self.root_url / 'users/') as response:
            return [from_dict(User, data) for data in await response.json()]

    async def get_user(self, id: int) -> User:
        async with self.session.get(self.root_url / f'users/{id}/') as response:
            return from_dict(User, await response.json(), config)

    async def create_user(self, data: CreateUser) -> User:
        async with self.session.post(self.root_url / 'users/', json=data) as response:
            return from_dict(User, await response.json(), config)

    async def get_database_records(
        self, search: str | None = None, has_data_path: str | None = None
    ) -> list[DatabaseRecord]:
        params: dict[str, str] = {}

        if search is not None:
            params['search'] = search
        if has_data_path is not None:
            params['has_data_path'] = has_data_path

        async with self.session.get(
            self.root_url / 'database-records/', params=params
        ) as response:
            return [from_dict(DatabaseRecord, data) for data in await response.json()]

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

        async with self.session.request(
            METH_PATCH if partial else METH_PUT,
            self.root_url / 'database-records/update-many/',
            params=params,
            json=data,
        ) as response:
            return [from_dict(DatabaseRecord, data) for data in await response.json()]

    async def get_database_record(self, id: int) -> DatabaseRecord:
        async with self.session.get(
            self.root_url / f'database-records/{id}/'
        ) as response:
            return from_dict(DatabaseRecord, await response.json(), config)

    async def create_database_record(
        self, data: CreateDatabaseRecord
    ) -> DatabaseRecord:
        async with self.session.post(
            self.root_url / 'database-records/', json=data
        ) as response:
            return from_dict(DatabaseRecord, await response.json(), config)

    async def update_database_record(
        self, id: int, data: UpdateDatabaseRecord
    ) -> DatabaseRecord:
        async with self.session.put(
            self.root_url / f'database-records/{id}/', json=data
        ) as response:
            return from_dict(DatabaseRecord, await response.json(), config)
