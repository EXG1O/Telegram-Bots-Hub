from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update, User

from service.enums import CommandKeyboardType
from service.models import Bot as ServiceBot
from service.models import Command
from service.models import User as ServiceUser

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, TypeVar
import asyncio

if TYPE_CHECKING:
	from .bot import Bot
else:
	Bot = Any


T = TypeVar('T')

Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


class CreateUserMiddleware(BaseMiddleware):
	async def __call__(  # type: ignore [override]
		self, handler: Handler, event: Update, data: dict[str, Any]
	) -> Any:
		event_from_user: User | None = data.get('event_from_user')

		if event_from_user:
			bot: Bot = data['bot']

			data['service_bot_user'] = await bot.api.create_user(
				{
					'telegram_id': event_from_user.id,
					'full_name': event_from_user.full_name,
				}
			)

			return await handler(event, data)


class CheckUserPermissionsMiddleware(BaseMiddleware):
	async def __call__(  # type: ignore [override]
		self, handler: Handler, event: Update, data: dict[str, Any]
	) -> Any:
		bot: Bot = data['bot']
		service_bot: ServiceBot = await bot.api.get_bot()
		service_bot_user: ServiceUser = data['service_bot_user']

		match (
			service_bot.is_private,
			service_bot_user.is_allowed,
			service_bot_user.is_blocked,
		):
			case (True, True, False) | (False, _, False):
				return await handler(event, data)


class SearchCommandMiddleware(BaseMiddleware):
	async def search_command_by_text(
		self,
		text: str,
		commands: list[Command],
	) -> Command | None:
		for command in commands:
			if command.trigger and command.trigger.text == text:
				return command

		return None

	async def search_command_by_keyboard_buttons_text(
		self,
		bot: Bot,
		text: str,
		commands: list[Command],
	) -> Command | None:
		for command in commands:
			if (
				command.keyboard
				and command.keyboard.type == CommandKeyboardType.DEFAULT
			):
				for button in command.keyboard.buttons:
					if button.text == text:
						return await bot.api.get_command(command.id)

		return None

	async def search_command_by_keyboard_buttons_id(
		self,
		bot: Bot,
		button_id: int,
		commands: list[Command],
	) -> Command | None:
		for command in commands:
			if command.keyboard and command.keyboard.type in [
				CommandKeyboardType.INLINE,
				CommandKeyboardType.PAYMENT,
			]:
				for button in command.keyboard.buttons:
					if button.id == button_id:
						return await bot.api.get_command(command.id)

		return None

	async def __call__(  # type: ignore [override]
		self, handler: Handler, event: Update, data: dict[str, Any]
	) -> Any:
		bot: Bot = data['bot']
		commands = await bot.api.get_commands()
		found_command: Command | None = None

		if isinstance(event.event, Message) and event.event.text:
			text: str = event.event.text
			text_search_result, keyboard_search_result = await asyncio.gather(
				self.search_command_by_text(text, commands),
				self.search_command_by_keyboard_buttons_text(bot, text, commands),
			)
			found_command = text_search_result or keyboard_search_result
		elif isinstance(event.event, CallbackQuery) and event.event.data:
			found_command = await self.search_command_by_keyboard_buttons_id(
				bot, int(event.event.data), commands
			)

		if found_command:
			data['command'] = found_command

			return await handler(event, data)
