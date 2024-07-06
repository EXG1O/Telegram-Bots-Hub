from bot import Bot

from . import settings
from .exceptions import (
	BotAlreadyEnabledError,
	NoSpaceForStartBotError,
	NotFoundBotError,
)

from typing import Literal

bots: dict[int, Bot] = {}


async def get_bot(bot_service_id: int) -> Bot:
	try:
		return bots[bot_service_id]
	except KeyError:
		raise NotFoundBotError()


async def set_bot_status(
	bot_service_id: int, status: Literal['online', 'offline']
) -> None:
	bot: Bot = await get_bot(bot_service_id)

	if status == 'online':
		await bot.api.update_bot(
			{
				'is_enabled': True,
				'is_loading': False,
			}
		)
	elif status == 'offline':
		await bot.api.update_bot(
			{
				'is_enabled': False,
				'is_loading': False,
			}
		)

		del bots[bot.service_id]


async def start_bot(bot_service_id: int, bot_token: str) -> None:
	if bot_service_id in bots:
		raise BotAlreadyEnabledError()

	if len(bots) >= settings.max_bots_limit:
		raise NoSpaceForStartBotError()

	bot = Bot(bot_service_id, bot_token)
	bots[bot_service_id] = bot

	await bot.start()


async def stop_bot(bot_service_id: int) -> None:
	bot: Bot = await get_bot(bot_service_id)
	await bot.stop()
