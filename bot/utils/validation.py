from telegram.models import User

from service.schemas import CreateUser
import service.models

from collections.abc import Awaitable
from typing import TYPE_CHECKING, Any, overload
import asyncio

if TYPE_CHECKING:
    from ..bot import Bot
else:
    Bot = Any


@overload
async def is_valid_user(bot: Bot, *, user: User) -> bool: ...
@overload
async def is_valid_user(
    bot: Bot,
    *,
    service_bot: service.models.Bot | None = None,
    service_user: service.models.User | None = None,
) -> bool: ...
async def is_valid_user(
    bot: Bot,
    *,
    user: User | None = None,
    service_bot: service.models.Bot | None = None,
    service_user: service.models.User | None = None,
) -> bool:
    if TYPE_CHECKING:
        get_service_user: Awaitable[service.models.User]

    if service_user:
        get_service_user = asyncio.sleep(0, result=service_user)
    else:
        if not user:
            raise ValueError(
                "The value for 'user' cannot be None if 'service_user' is None."
            )

        get_service_user = bot.service.create_user(
            CreateUser(telegram_id=user.id, full_name=user.full_name)
        )

    service_bot, service_user = await asyncio.gather(
        (
            asyncio.sleep(0, result=service_bot)
            if service_bot
            else bot.service.get_bot()
        ),
        get_service_user,
    )
    assert service_bot and service_user

    return not (
        service_user.is_blocked
        or service_bot.is_private
        and not service_user.is_allowed
    )
