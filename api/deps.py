from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import APIKeyHeader

from core import dispatcher
from core.exceptions import NotFoundBotError
from core.settings import SELF_TELEGRAM_TOKEN, SELF_TOKEN

from typing import Annotated

self_token_header = APIKeyHeader(name='X-API-KEY')
telegram_token_header = APIKeyHeader(name='X-Telegram-Bot-Api-Secret-Token')


async def verify_self_token(token: Annotated[str, Depends(self_token_header)]) -> str:
	if token != SELF_TOKEN:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

	return token


async def verify_telegram_token(
	token: Annotated[str, Depends(telegram_token_header)],
) -> str:
	if token != SELF_TELEGRAM_TOKEN:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

	return token


async def check_bot_service_id(id: int) -> int:
	if id not in dispatcher.bots:
		raise NotFoundBotError()

	return id


BotServiceID = Annotated[int, Depends(check_bot_service_id)]
