from fastapi import APIRouter

from core import dispatcher

from ...enums import Tag
from .schemas import StartBotRequest

router = APIRouter(prefix='/bots', tags=[Tag.BOTS])


@router.get('/')
async def get_bots() -> list[int]:
	return list(dispatcher.bots)


@router.post('/{bot_service_id}/start/')
async def start_bot(bot_service_id: int, request: StartBotRequest) -> None:
	await dispatcher.start_bot(bot_service_id, request.bot_token)


@router.post('/{bot_service_id}/restart/')
async def restart_bot(bot_service_id: int) -> None:
	await dispatcher.restart_bot(bot_service_id)


@router.post('/{bot_service_id}/stop/')
async def stop_bot(bot_service_id: int) -> None:
	await dispatcher.stop_bot(bot_service_id)
