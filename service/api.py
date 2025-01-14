from aiohttp.typedefs import LooseHeaders
from dacite import Config, from_dict
from yarl import URL
import aiohttp
import aiohttp.typedefs

from core import settings

from .models import BackgroundTask, Bot, Command, Condition, User, Variable
from .schemas import CreateUserData

config = Config(check_types=False)

HEADERS: LooseHeaders = {'Authorization': f'Token {settings.SERVICE_TOKEN}'}


class API:
	"""Bot API for getting data from the main service."""

	def __init__(self, bot_service_id: int) -> None:
		self.root_url: URL = (
			settings.SERVICE_URL
			/ f'api/telegram-bots-hub/telegram-bots/{bot_service_id}/'
		)
		self.session = aiohttp.ClientSession(headers=HEADERS, raise_for_status=True)

	async def get_bot(self) -> Bot:
		async with self.session.get(self.root_url) as response:
			return from_dict(Bot, await response.json(), config)

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
		async with self.session.get(self.root_url / 'background_tasks/') as response:
			return [
				from_dict(BackgroundTask, data, config)
				for data in await response.json()
			]

	async def get_background_task(self, background_task_id: int) -> BackgroundTask:
		async with self.session.get(
			f'background_tasks/{background_task_id}/'
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
