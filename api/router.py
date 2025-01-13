from fastapi import APIRouter, Depends

from core import dispatcher

from .deps import (
	BotServiceID,
	verify_self_token,
	verify_telegram_token,
)
from .schemas import StartBotRequest

from typing import Any

router = APIRouter()
bots_router = APIRouter(prefix='/bots', dependencies=[Depends(verify_self_token)])
telegram_router = APIRouter(
	prefix='/telegram/bots', dependencies=[Depends(verify_telegram_token)]
)


@bots_router.get('/')
async def get_bots() -> list[int]:
	return list(dispatcher.bots)


@bots_router.post('/{bot_service_id}/start/')
async def start_bot(bot_service_id: int, request: StartBotRequest) -> None:
	await dispatcher.start_bot(bot_service_id, request.bot_token)


@bots_router.post('/{bot_service_id}/restart/')
async def restart_bot(bot_service_id: BotServiceID) -> None:
	await dispatcher.restart_bot(bot_service_id)


@bots_router.post('/{bot_service_id}/stop/')
async def stop_bot(bot_service_id: BotServiceID) -> None:
	await dispatcher.stop_bot(bot_service_id)


@telegram_router.post('/{bot_service_id}/webhook/')
async def bot_webhook(bot_service_id: BotServiceID, request: Any) -> None:
	await dispatcher.feed_bot_webhook_update(bot_service_id, request)


router.include_router(bots_router)
router.include_router(telegram_router)
