from telegram import User

from service.schemas import CreateUser
import service.models

from collections.abc import Awaitable
from typing import TYPE_CHECKING, Any
import asyncio

if TYPE_CHECKING:
    from ..bot import Bot
else:
    Bot = Any


async def is_valid_user(
    bot: Bot,
    user: User | None = None,
    service_bot: service.models.Bot | None = None,
    service_user: service.models.User | None = None,
) -> bool:
    if TYPE_CHECKING:
        create_service_user: Awaitable[service.models.User]

    if not service_user:
        if not user:
            raise ValueError(
                "The value for 'user' cannot be None if the value "
                "for 'service_user' is also None."
            )

        create_service_user = bot.service_api.create_user(
            CreateUser(telegram_id=user.id, full_name=user.full_name)
        )
    else:
        create_service_user = asyncio.sleep(0, result=service_user)

    service_bot, service_user = await asyncio.gather(
        bot.service_api.get_bot(),
        create_service_user,
    )
    assert service_bot
    assert service_user

    return not (
        service_user.is_blocked
        or service_bot.is_private
        and not service_user.is_allowed
    )
