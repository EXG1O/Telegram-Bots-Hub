from aiogram import Dispatcher as BaseDispatcher
from aiogram import loggers
from aiogram.methods import GetUpdates
from aiogram.types import Update, User

from core import dispatcher

from collections.abc import AsyncGenerator, Coroutine
from typing import TYPE_CHECKING, Any
import asyncio

if TYPE_CHECKING:
	from .bot import Bot
else:
	Bot = Any


class Dispatcher(BaseDispatcher):
	async def _listen_updates(self, bot: Bot) -> AsyncGenerator[Update, None]:  # type: ignore [override]
		"""Endless updates reader"""

		polling_timeout: int = 30
		get_updates = GetUpdates(timeout=polling_timeout)
		kwargs: dict[str, Any] = {}

		if bot.session.timeout:
			kwargs['request_timeout'] = int(bot.session.timeout + polling_timeout)

		while True:
			try:
				updates = await bot(get_updates, **kwargs)
			except:  # noqa: E722
				break

			if updates is None:
				continue

			for update in updates:
				yield update

				get_updates.offset = update.update_id + 1

	async def _polling(self, bot: Bot, **kwargs: Any) -> None:  # type: ignore [override]
		user: User = await bot.me()

		await dispatcher.set_bot_status(bot.service_id, 'online')

		loggers.dispatcher.info(
			'Run polling for bot @%s id=%d - %r',
			user.username,
			bot.id,
			user.full_name,
		)

		keys_to_remove: list[str] = [
			'polling_timeout',
			'handle_as_tasks',
			'backoff_config',
			'allowed_updates',
		]

		for key in keys_to_remove:
			try:
				del kwargs[key]
			except KeyError:
				pass

		try:
			async for update in self._listen_updates(bot):
				handle_update: Coroutine[Any, Any, bool] = self._process_update(
					bot=bot, update=update, **kwargs
				)
				handle_update_task: asyncio.Task[bool] = asyncio.create_task(
					handle_update
				)
				self._handle_update_tasks.add(handle_update_task)
				handle_update_task.add_done_callback(self._handle_update_tasks.discard)
		finally:
			await dispatcher.set_bot_status(bot.service_id, 'offline')

			loggers.dispatcher.info(
				'Polling stopped for bot @%s id=%d - %r',
				user.username,
				bot.id,
				user.full_name,
			)

	async def start_polling(self, bot: Bot) -> None:  # type: ignore [override]
		"""Polling runner"""

		return await super().start_polling(bot)
