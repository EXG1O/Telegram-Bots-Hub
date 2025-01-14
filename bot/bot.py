from telegram import (
	BotCommand,
	CallbackQuery,
	Chat,
	InlineKeyboardMarkup,
	InputMediaDocument,
	InputMediaPhoto,
	MaybeInaccessibleMessage,
	Message,
	ReplyKeyboardMarkup,
	Update,
	User,
)
from telegram.constants import ParseMode, UpdateType
from telegram.ext import (
	ApplicationBuilder,
	CallbackQueryHandler,
	ContextTypes,
	Defaults,
	MessageHandler,
	filters,
)

from core.settings import SELF_URL, SERVICE_URL, TELEGRAM_TOKEN
from service import API
import service.enums
import service.models

from .utils import process_text_with_html_tags

from typing import Any
import re
import string


class Bot:
	def __init__(self, service_id: int, token: str):
		self.app = (
			ApplicationBuilder()
			.token(token)
			.defaults(Defaults(parse_mode=ParseMode.HTML))
			.updater(None)
			.build()
		)

		self.service_id = service_id
		self.service_api = API(service_id)
		self.last_messages: dict[int, list[Message]] = {}

	async def find_command(
		self, text: str | None = None, button_id: int | None = None
	) -> service.models.Command | None:
		commands: list[service.models.Command] = await self.service_api.get_commands()

		if text:
			for command in commands:
				if (command.trigger and command.trigger.text == text) or (
					command.keyboard
					and command.keyboard.type
					== service.enums.CommandKeyboardType.DEFAULT
					and any(btn.text == text for btn in command.keyboard.buttons)
				):
					return command
		elif button_id:
			for command in commands:
				if (
					command.keyboard
					and command.keyboard.type
					in [
						service.enums.CommandKeyboardType.INLINE,
						service.enums.CommandKeyboardType.PAYMENT,
					]
					and any(btn.id == button_id for btn in command.keyboard.buttons)
				):
					return command

		return None

	async def handle_update(
		self, update: Update, context: ContextTypes.DEFAULT_TYPE
	) -> None:
		command: service.models.Command | None = await self.find_command(
			text=(update.message.text if update.message else None),
			button_id=(
				int(update.callback_query.data)
				if update.callback_query and update.callback_query.data
				else None
			),
		)

		if not command:
			return None

		callback_query: CallbackQuery | None = update.callback_query
		message: Message | MaybeInaccessibleMessage | None = (
			callback_query.message if callback_query else update.message
		)

		if not message:
			return None

		chat: Chat | None = update.effective_chat
		user: User | None = update.effective_user

		if not chat or not user:
			return None

		message_text: str = await process_text_with_html_tags(command.message.text)
		keyboard: ReplyKeyboardMarkup | InlineKeyboardMarkup | None = None
		reply_to_message_id: int | None = None

		if command.settings.is_reply_to_user_message:
			reply_to_message_id = message.message_id

		if command.settings.is_send_as_new_message:
			await chat.delete_messages(
				[last_message.id for last_message in self.last_messages.pop(chat.id)]
			)

		kwargs: dict[str, Any] = {'reply_to_message_id': reply_to_message_id}
		images: list[InputMediaPhoto] = [
			InputMediaPhoto(str(SERVICE_URL / url[1:]))
			for image in command.images
			if (url := image.url or image.from_url)
		][:10]
		files: list[InputMediaDocument] = [
			InputMediaDocument(str(SERVICE_URL / url[1:]))
			for file in command.files
			if (url := file.url or file.from_url)
		][:10]

		image_count: int = len(images)
		file_count: int = len(files)
		new_bot_messages: list[Message] = []

		if image_count == 1 and file_count == 1:
			new_bot_messages += [
				await chat.send_photo(images[0].media, **kwargs),  # type: ignore [arg-type]
				await chat.send_document(files[0].media, **kwargs),  # type: ignore [arg-type]
				await chat.send_message(message_text, reply_markup=keyboard, **kwargs),
			]
		elif image_count > 1 and file_count == 1:
			new_bot_messages.extend(await chat.send_media_group(images, **kwargs))
			new_bot_messages.append(
				await chat.send_document(
					files[0].media,  # type: ignore [arg-type]
					caption=message_text,
					reply_markup=keyboard,
					**kwargs,
				)
			)
		elif image_count == 1 and file_count > 1:
			new_bot_messages.extend(await chat.send_media_group(files, **kwargs))
			new_bot_messages.append(
				await chat.send_photo(
					images[0].media,  # type: ignore [arg-type]
					message_text,
					reply_markup=keyboard,
					**kwargs,
				)
			)
		elif image_count > 1 and file_count > 1:
			new_bot_messages.extend(await chat.send_media_group(images, **kwargs))
			new_bot_messages.extend(await chat.send_media_group(files, **kwargs))
			new_bot_messages.append(
				await chat.send_message(message_text, reply_markup=keyboard, **kwargs)
			)
		elif image_count == 1:
			new_bot_messages.append(
				await chat.send_photo(
					images[0].media,  # type: ignore [arg-type]
					message_text,
					reply_markup=keyboard,
					**kwargs,
				)
			)
		elif file_count == 1:
			new_bot_messages.append(
				await chat.send_document(
					files[0].media,  # type: ignore [arg-type]
					caption=message_text,
					reply_markup=keyboard,
					**kwargs,
				)
			)
		else:
			new_bot_messages.append(
				await chat.send_message(message_text, reply_markup=keyboard, **kwargs)
			)

		if not user.is_bot and command.settings.is_delete_user_message:
			await chat.delete_message(message.message_id)

	async def feed_webhook_update(self, update: Update) -> None:
		user: User | None = update.effective_user

		if not user:
			return None

		service_bot: service.models.Bot = await self.service_api.get_bot()
		service_user: service.models.User = await self.service_api.create_user(
			{'telegram_id': user.id, 'full_name': user.full_name}
		)

		match (
			service_bot.is_private,
			service_user.is_allowed,
			service_user.is_blocked,
		):
			case (True, True, False) | (False, _, False):
				await self.app.update_queue.put(update)

	async def setup(self) -> None:
		await self.app.bot.set_my_commands(
			[
				BotCommand(
					command=re.sub(f'[{string.punctuation}]', '', command.trigger.text),
					description=command.trigger.description,
				)
				for command in await self.service_api.get_commands()
				if command.trigger and command.trigger.description
			]
		)

	async def start(self) -> None:
		await self.setup()

		self.app.add_handler(MessageHandler(filters.TEXT, self.handle_update))
		self.app.add_handler(CallbackQueryHandler(self.handle_update))

		await self.app.bot.set_webhook(
			f'{SELF_URL}/bots/{self.service_id}/webhook/',
			allowed_updates=[UpdateType.MESSAGE, UpdateType.CALLBACK_QUERY],
			secret_token=TELEGRAM_TOKEN,
		)

		await self.app.initialize()
		await self.app.start()

	async def stop(self) -> None:
		try:
			await self.app.bot.delete_webhook()
		finally:
			await self.service_api.session.close()
			await self.app.stop()
			await self.app.shutdown()
