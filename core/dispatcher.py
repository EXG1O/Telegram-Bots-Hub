from aiogram.types import Update

from bot import Bot

from .exceptions import BotAlreadyEnabledError, NotFoundBotError

bots: dict[int, Bot] = {}


async def get_bot(bot_service_id: int) -> Bot:
	try:
		return bots[bot_service_id]
	except KeyError:
		raise NotFoundBotError()


async def start_bot(bot_service_id: int, bot_token: str) -> None:
	if bot_service_id in bots:
		raise BotAlreadyEnabledError()

	bot = Bot(bot_service_id, bot_token)
	bots[bot_service_id] = bot

	await bot.start()


async def restart_bot(bot_service_id: int) -> None:
	bot: Bot = await get_bot(bot_service_id)
	await bot.restart()


async def stop_bot(bot_service_id: int) -> None:
	bot: Bot = await get_bot(bot_service_id)
	await bot.stop()


async def feed_bot_webhook_update(bot_service_id: int, update: Update) -> None:
	bot: Bot = await get_bot(bot_service_id)
	await bot.dispatcher.feed_webhook_update(bot, update)
