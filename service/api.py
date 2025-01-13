from dacite import from_dict
from yarl import URL
import aiohttp

from core import settings

from .models import BackgroundTask, Bot, Command, Condition, User, Variable
from .schemas import CreateUserData

HEADERS = {'Authorization': f'Token {settings.SERVICE_TOKEN}'}


class API:
	"""Bot API for getting data from the main service."""

	def __init__(self, bot_service_id: int) -> None:
		self.session = aiohttp.ClientSession(
			URL(
				settings.SERVICE_URL
				+ f'/api/telegram-bots-hub/telegram-bots/{bot_service_id}'
			),
			headers=HEADERS,
			raise_for_status=True,
		)

	async def get_bot(self) -> Bot:
		async with self.session.get('/') as response:
			return from_dict(Bot, await response.json())

	async def get_commands(self) -> list[Command]:
		async with self.session.get('/commands') as response:
			return [from_dict(Command, data) for data in await response.json()]

	async def get_command(self, command_id: int) -> Command:
		async with self.session.get(f'/commands/{command_id}') as response:
			return from_dict(Command, await response.json())

	async def get_conditions(self) -> list[Condition]:
		async with self.session.get('/conditions') as response:
			return [from_dict(Condition, data) for data in await response.json()]

	async def get_condition(self, condition_id: int) -> Condition:
		async with self.session.get(f'/conditions/{condition_id}') as response:
			return from_dict(Condition, await response.json())

	async def get_background_tasks(self) -> list[BackgroundTask]:
		async with self.session.get('/background_tasks') as response:
			return [from_dict(BackgroundTask, data) for data in await response.json()]

	async def get_background_task(self, background_task_id: int) -> BackgroundTask:
		async with self.session.get(
			f'/background_tasks/{background_task_id}'
		) as response:
			return from_dict(BackgroundTask, await response.json())

	async def get_variables(self) -> list[Variable]:
		async with self.session.get('/variables') as response:
			return [from_dict(Variable, data) for data in await response.json()]

	async def get_variable(self, variable_id: int) -> Variable:
		async with self.session.get(f'/variables/{variable_id}') as response:
			return from_dict(Variable, await response.json())

	async def get_users(self) -> list[User]:
		async with self.session.get('/users') as response:
			return [from_dict(User, data) for data in await response.json()]

	async def get_user(self, user_id: int) -> User:
		async with self.session.get(f'/users/{user_id}') as response:
			return from_dict(User, await response.json())

	async def create_user(self, data: CreateUserData) -> User:
		async with self.session.post('/users', data=data) as response:
			return from_dict(User, await response.json())
