from fastapi import APIRouter

from bot import Bot

from .. import dispatcher
from ..models import (
	RestartBotRequest,
	SendMessageRequest,
	StartBotRequest,
)

router = APIRouter(prefix='/bots', tags=['bots'])


@router.get('/')
async def get_bots() -> list[int]:
	return list(dispatcher.bots)


@router.post('/{bot_service_id}/start/')
async def start_bot(bot_service_id: int, request: StartBotRequest) -> None:
	await dispatcher.start_bot(bot_service_id, request.bot_token)


@router.post('/{bot_service_id}/restart/')
async def restart_bot(bot_service_id: int, request: RestartBotRequest) -> None:
	await dispatcher.stop_bot(bot_service_id)
	await dispatcher.start_bot(bot_service_id, request.bot_token)


@router.post('/{bot_service_id}/stop/')
async def stop_bot(bot_service_id: int) -> None:
	await dispatcher.stop_bot(bot_service_id)


@router.post('/chats/{chat_id}/send-message/')
async def bot_send_message(
	bot_service_id: int, chat_id: int, request: SendMessageRequest
) -> None:
	bot: Bot = await dispatcher.get_bot(bot_service_id)
	await bot.send_message(chat_id, request.message_text)
