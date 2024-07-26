from aiogram import Bot as BaseBot
from aiogram import Dispatcher
from aiogram.enums import ParseMode
from aiogram.exceptions import (
	RestartingTelegram,
	TelegramEntityTooLarge,
	TelegramForbiddenError,
	TelegramMigrateToChat,
	TelegramNetworkError,
	TelegramNotFound,
	TelegramRetryAfter,
	TelegramServerError,
)
from aiogram.methods import TelegramMethod
from aiogram.types import BotCommand as BotMenuCommand
from aiogram.types import (
	CallbackQuery,
	Chat,
	InlineKeyboardMarkup,
	InputMediaDocument,
	InputMediaPhoto,
	Message,
	ReplyKeyboardMarkup,
	URLInputFile,
	User,
)

from service import API
from service.data import Command

from .middlewares import (
	CheckUserPermissionsMiddleware,
	CreateUserMiddleware,
	SearchCommandMiddleware,
)

from typing import Any, TypeVar
import asyncio
import re
import string

T = TypeVar('T')


class Bot(BaseBot):
	def __init__(self, service_id: int, token: str) -> None:
		super().__init__(token, parse_mode=ParseMode.HTML)

		self.service_id = service_id

		self.api = API(service_id)
		self.dispatcher = Dispatcher()
		self.last_messages: dict[int, list[Message]] = {}

	async def __call__(  # type: ignore [override]
		self, method: TelegramMethod[T], *args: Any, **kwargs: Any
	) -> T | None:
		try:
			result: T | None = await super().__call__(method, *args, **kwargs)  # type: ignore [arg-type]
		except TelegramRetryAfter as exception:
			await asyncio.sleep(exception.retry_after)
			await self.__call__(method, *args, **kwargs)
		except (
			TelegramNetworkError,
			TelegramServerError,
			TelegramForbiddenError,
			RestartingTelegram,
			TelegramNotFound,
			TelegramMigrateToChat,
			TelegramEntityTooLarge,
		):
			return None

		if result:
			if isinstance(result, list):
				for instance in result:
					if isinstance(instance, Message):
						self.last_messages.setdefault(instance.chat.id, []).append(
							instance
						)
			elif isinstance(result, Message):
				self.last_messages.setdefault(result.chat.id, []).append(result)

		return result  # type: ignore [return-value]

	async def get_last_messages(self, chat_id: int) -> list[Message]:
		return self.last_messages.setdefault(chat_id, [])

	async def delete_last_messages(self, chat_id: int) -> None:
		last_messages: list[Message] = await self.get_last_messages(chat_id)

		for index, last_message in enumerate(last_messages.copy()):
			try:
				await last_message.delete()
			finally:
				del last_messages[index]

	async def generate_variables(self, message: Message, user: User) -> dict[str, Any]:
		bot: User = await self.me()

		return {
			'BOT_NAME': bot.full_name,
			'BOT_USERNAME': bot.username,
			'USER_ID': user.id,
			'USER_USERNAME': user.username,
			'USER_FIRST_NAME': user.first_name,
			'USER_LAST_NAME': user.last_name,
			'USER_FULL_NAME': user.full_name,
			'USER_LANGUAGE_CODE': user.language_code,
			'USER_MESSAGE_ID': message.message_id,
			'USER_MESSAGE_TEXT': message.text,
			'USER_MESSAGE_DATE': message.date,
			**{
				variable.name: variable.value
				for variable in await self.api.get_variables()
			},
		}

	async def answer(
		self,
		event: Message,
		chat: Chat,
		user: User,
		command: Command,
		keyboard: ReplyKeyboardMarkup | InlineKeyboardMarkup | None = None,
	) -> None:
		reply_to_message_id: int | None = None

		if command.settings.is_reply_to_user_message:
			reply_to_message_id = event.message_id

		if command.settings.is_send_as_new_message:
			await self.delete_last_messages(chat.id)

		kwargs: dict[str, Any] = {'reply_to_message_id': reply_to_message_id}
		images: list[InputMediaPhoto] = [
			InputMediaPhoto(media=URLInputFile(url, filename=image.name))
			for image in command.images
			if (url := image.url or image.from_url)
		][:10]
		files: list[InputMediaDocument] = [
			InputMediaDocument(media=URLInputFile(url, filename=file.name))
			for file in command.files
			if (url := file.url or file.from_url)
		][:10]

		if len(images) == 1 and len(files) == 1:
			await event.answer_photo(images[0].media, **kwargs)
			await event.answer_document(files[0].media, **kwargs)
			await event.answer(
				command.message.text,
				reply_markup=keyboard,
				**kwargs,
			)
		elif len(images) > 1 and len(files) == 1:
			await event.answer_media_group(images, **kwargs)  # type: ignore [arg-type]
			await event.answer_document(
				files[0].media,
				caption=command.message.text,
				reply_markup=keyboard,
				**kwargs,
			)
		elif len(images) == 1 and len(files) > 1:
			await event.answer_media_group(files, **kwargs)  # type: ignore [arg-type]
			await event.answer_photo(
				images[0].media,
				command.message.text,
				reply_markup=keyboard,
				**kwargs,
			)
		elif len(images) > 1 and len(files) > 1:
			await event.answer_media_group(images, **kwargs)  # type: ignore [arg-type]
			await event.answer_media_group(files, **kwargs)  # type: ignore [arg-type]
			await event.answer(
				command.message.text,
				reply_markup=keyboard,
				**kwargs,
			)
		elif len(images) == 1:
			await event.answer_photo(
				images[0].media,
				command.message.text,
				reply_markup=keyboard,
				**kwargs,
			)
		elif len(files) == 1:
			await event.answer_document(
				files[0].media,
				caption=command.message.text,
				reply_markup=keyboard,
				**kwargs,
			)
		else:
			await event.answer(
				command.message.text,
				reply_markup=keyboard,
				**kwargs,
			)

		if not user.is_bot and command.settings.is_delete_user_message:
			await event.delete()

	async def message_handler(
		self,
		event: Message,
		event_chat: Chat,
		event_from_user: User,
		command: Command,
		**kwargs: Any,
	) -> None:
		await self.answer(
			event,
			event_chat,
			event_from_user,
			command,
		)

	async def callback_query_handler(
		self,
		event: CallbackQuery,
		event_chat: Chat,
		event_from_user: User,
		command: Command,
		**kwargs: Any,
	) -> None:
		if not isinstance(event.message, Message):
			return

		await self.answer(
			event.message,
			event_chat,
			event_from_user,
			command,
		)

	async def setup(self) -> None:
		await self.set_my_commands(
			[
				BotMenuCommand(
					command=re.sub(f'[{string.punctuation}]', '', command.trigger.text),
					description=command.trigger.description,
				)
				for command in await self.api.get_commands()
				if command.trigger and command.trigger.description
			]
		)

		self.dispatcher.update.outer_middleware.register(CreateUserMiddleware())
		self.dispatcher.update.outer_middleware.register(
			CheckUserPermissionsMiddleware()
		)
		self.dispatcher.update.outer_middleware.register(SearchCommandMiddleware())

		self.dispatcher.message.register(self.message_handler)
		self.dispatcher.callback_query.register(self.callback_query_handler)

	async def start(self) -> None:
		await self.setup()
		asyncio.create_task(self.dispatcher.start_polling(self))

	async def restart(self) -> None:
		await self.setup()

	async def stop(self) -> None:
		await self.dispatcher.stop_polling()
		await self.api.session.close()
