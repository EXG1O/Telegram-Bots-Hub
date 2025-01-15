from fastapi import APIRouter, Depends, Request

from telegram import Update
from telegram.error import TelegramError

from bot import Bot
from core.storage import bots

from .deps import BotServiceID, verify_self_token, verify_telegram_token
from .exceptions import BotAlreadyEnabledError
from .schemas import StartBotRequest

router = APIRouter()
bots_router = APIRouter(prefix='/bots', dependencies=[Depends(verify_self_token)])


@bots_router.get('/')
async def get_bots() -> list[int]:
	return list(bots)


@bots_router.post('/{bot_service_id}/start/')
async def start_bot(bot_service_id: int, request: StartBotRequest) -> None:
	if bot_service_id in bots:
		raise BotAlreadyEnabledError()

	bot = Bot(bot_service_id, request.bot_token)
	bots[bot_service_id] = bot

	try:
		await bot.start()
	except TelegramError:
		del bots[bot_service_id]


@bots_router.post('/{bot_service_id}/restart/')
async def restart_bot(bot_service_id: BotServiceID) -> None:
	old_bot: Bot = bots[bot_service_id]

	bot = Bot(bot_service_id, old_bot.app.bot.token)
	bots[bot_service_id] = bot

	try:
		await bot.start()
	except TelegramError:
		del bots[bot_service_id]


@bots_router.post('/{bot_service_id}/stop/')
async def stop_bot(bot_service_id: BotServiceID) -> None:
	await bots.pop(bot_service_id).stop()


@router.post(
	'/bots/{bot_service_id}/webhook/', dependencies=[Depends(verify_telegram_token)]
)
async def bot_webhook(bot_service_id: BotServiceID, request: Request) -> None:
	bot: Bot = bots[bot_service_id]
	update: Update | None = Update.de_json(await request.json(), bot.app.bot)

	if update:
		await bot.feed_webhook_update(update)


router.include_router(bots_router)
