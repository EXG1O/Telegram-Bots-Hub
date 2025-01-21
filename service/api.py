from aiohttp import ClientSession, UnixConnector
from aiohttp.typedefs import LooseHeaders
from dacite import Config, from_dict
from yarl import URL

from core.settings import SERVICE_TOKEN, SERVICE_UNIX_SOCK, SERVICE_URL

from .enums import (
    APIRequestMethod,
    BackgroundTaskInterval,
    CommandKeyboardType,
    ConditionPartNextPartOperator,
    ConditionPartOperator,
    ConditionPartType,
    ConnectionSourceObjectType,
    ConnectionTargetObjectType,
)
from .models import (
    BackgroundTask,
    Bot,
    Command,
    CommandKeyboardButton,
    CommandTrigger,
    Condition,
    DatabaseRecord,
    User,
    Variable,
)
from .schemas import CreateDatabaseRecord, CreateUserData

from typing import Final

config = Config(
    type_hooks={
        ConnectionSourceObjectType: ConnectionSourceObjectType,
        ConnectionTargetObjectType: ConnectionTargetObjectType,
        APIRequestMethod: APIRequestMethod,
        CommandKeyboardType: CommandKeyboardType,
        ConditionPartType: ConditionPartType,
        ConditionPartOperator: ConditionPartOperator,
        ConditionPartNextPartOperator: ConditionPartNextPartOperator,
        BackgroundTaskInterval: BackgroundTaskInterval,
    }
)

HEADERS: Final[LooseHeaders] = {'Authorization': f'Token {SERVICE_TOKEN}'}


class API:
    """Bot API for getting data from the main service."""

    def __init__(self, bot_service_id: int) -> None:
        self.root_url: URL = (
            SERVICE_URL / f'api/telegram-bots-hub/telegram-bots/{bot_service_id}/'
        )
        self.session = ClientSession(
            # Don't move the init of the `UnixConnector` class outside of this class, ...
            # because it will cause an error when sending requests.
            connector=UnixConnector(path=str(SERVICE_UNIX_SOCK))
            if SERVICE_UNIX_SOCK
            else None,
            headers=HEADERS,
            raise_for_status=True,
        )

    async def get_bot(self) -> Bot:
        async with self.session.get(self.root_url) as response:
            return from_dict(Bot, await response.json(), config)

    async def get_command_triggers(
        self, text: str | None = None
    ) -> list[CommandTrigger]:
        url: URL = self.root_url / 'command-triggers/'

        if text:
            url = url.update_query({'text': text})

        async with self.session.get(url) as response:
            return [
                from_dict(CommandTrigger, data, config)
                for data in await response.json()
            ]

    async def get_commands_keyboard_buttons(
        self, id: int | None = None, text: str | None = None
    ) -> list[CommandKeyboardButton]:
        query_params: dict[str, str | int] = {}
        url: URL = self.root_url / 'commands-keyboard-buttons/'

        if id:
            query_params['id'] = id

        if text:
            query_params['text'] = text

        async with self.session.get(url % query_params) as response:
            return [
                from_dict(CommandKeyboardButton, data, config)
                for data in await response.json()
            ]

    async def get_commands(self) -> list[Command]:
        async with self.session.get(self.root_url / 'commands/') as response:
            return [from_dict(Command, data, config) for data in await response.json()]

    async def get_command(self, command_id: int) -> Command:
        async with self.session.get(
            self.root_url / f'commands/{command_id}/'
        ) as response:
            return from_dict(Command, await response.json(), config)

    async def get_conditions(self) -> list[Condition]:
        async with self.session.get(self.root_url / 'conditions/') as response:
            return [
                from_dict(Condition, data, config) for data in await response.json()
            ]

    async def get_condition(self, condition_id: int) -> Condition:
        async with self.session.get(
            self.root_url / f'conditions/{condition_id}/'
        ) as response:
            return from_dict(Condition, await response.json(), config)

    async def get_background_tasks(self) -> list[BackgroundTask]:
        async with self.session.get(self.root_url / 'background-tasks/') as response:
            return [
                from_dict(BackgroundTask, data, config)
                for data in await response.json()
            ]

    async def get_background_task(self, background_task_id: int) -> BackgroundTask:
        async with self.session.get(
            f'background-tasks/{background_task_id}/'
        ) as response:
            return from_dict(BackgroundTask, await response.json(), config)

    async def get_variables(self) -> list[Variable]:
        async with self.session.get(self.root_url / 'variables/') as response:
            return [from_dict(Variable, data, config) for data in await response.json()]

    async def get_variable(self, variable_id: int) -> Variable:
        async with self.session.get(
            self.root_url / f'variables/{variable_id}/'
        ) as response:
            return from_dict(Variable, await response.json(), config)

    async def get_users(self) -> list[User]:
        async with self.session.get(self.root_url / 'users/') as response:
            return [from_dict(User, data) for data in await response.json()]

    async def get_user(self, user_id: int) -> User:
        async with self.session.get(self.root_url / f'users/{user_id}/') as response:
            return from_dict(User, await response.json(), config)

    async def create_user(self, data: CreateUserData) -> User:
        async with self.session.post(self.root_url / 'users/', data=data) as response:
            return from_dict(User, await response.json(), config)

    async def get_database_records(self) -> list[DatabaseRecord]:
        async with self.session.get(self.root_url / 'database-records/') as response:
            return [from_dict(DatabaseRecord, data) for data in await response.json()]

    async def get_database_record(self, database_id: int) -> DatabaseRecord:
        async with self.session.get(
            self.root_url / f'database-records/{database_id}/'
        ) as response:
            return from_dict(DatabaseRecord, await response.json(), config)

    async def create_database_record(
        self, data: CreateDatabaseRecord
    ) -> DatabaseRecord:
        async with self.session.post(
            self.root_url / 'database-records/', data=data
        ) as response:
            return from_dict(DatabaseRecord, await response.json(), config)
