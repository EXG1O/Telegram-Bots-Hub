from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import APIKeyHeader

from api.exceptions import BotNotFoundError
from bot import Bot
from core.settings import APP_TOKEN
from core.storage import bots

from typing import Annotated
import secrets

token_header = APIKeyHeader(name='X-API-KEY')


async def verify_token(token: Annotated[str, Depends(token_header)]) -> str:
    if not secrets.compare_digest(token, APP_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return token


async def get_bot(service_id: int) -> Bot:
    bot: Bot | None = bots.get(service_id)

    if not bot:
        raise BotNotFoundError()

    return bot


ValidBot = Annotated[Bot, Depends(get_bot)]
