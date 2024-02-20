from core import settings

from .types import (
	ServiceBot,
	UpdateServiceBotData,
	ServiceBotCommand,
	ServiceBotVariable,
	ServiceBotUser,
)

from dacite import from_dict
import aiohttp


HEADERS = {'Authorization': f'Token {settings.service_token}'}


class API:
	def __init__(self, bot_service_id: int) -> None:
		self.url = f'/api/telegram-bots/hub/{bot_service_id}'
		self.session = aiohttp.ClientSession('http://127.0.0.1:8000', headers=HEADERS)

	async def get_bot(self) -> ServiceBot:
		async with self.session.get(f'{self.url}/') as response:
			response.raise_for_status()

			return from_dict(ServiceBot, await response.json())

	async def update_bot(self, data: UpdateServiceBotData) -> ServiceBot:
		async with self.session.patch(f'{self.url}/', data=data) as response:
			response.raise_for_status()

			return from_dict(ServiceBot, await response.json())

	async def get_bot_commands(self) -> list[ServiceBotCommand]:
		async with self.session.get(f'{self.url}/commands/') as response:
			response.raise_for_status()

			return [from_dict(ServiceBotCommand, data) for data in await response.json()]

	async def get_bot_command(self, command_service_id: int) -> ServiceBotCommand:
		async with self.session.get(f'{self.url}/commands/{command_service_id}') as response:
			response.raise_for_status()

			return from_dict(ServiceBotCommand, await response.json())

	async def get_bot_variables(self) -> list[ServiceBotVariable]:
		async with self.session.get(f'{self.url}/variables/') as response:
			response.raise_for_status()

			return [from_dict(ServiceBotVariable, data) for data in await response.json()]

	async def create_bot_user(self, user_telegram_id: int, user_full_name: str) -> ServiceBotUser:
		async with self.session.post(
			f'{self.url}/users/',
			data={
				'telegram_id': user_telegram_id,
				'full_name': user_full_name,
			},
		) as response:
			response.raise_for_status()

			return from_dict(ServiceBotUser, await response.json())