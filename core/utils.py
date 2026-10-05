from collections.abc import Awaitable
from typing import Any


def build_user_agent(**attributes: Any) -> str:
    base: str = 'ConstructorTelegramBots (constructor.exg1o.org'
    if attributes:
        return f'{base}; {"; ".join(f"{key}={value}" for key, value in attributes.items())})'
    return f'{base})'


async def safe_call[T](coro: Awaitable[T]) -> T | Exception:
    try:
        return await coro
    except Exception as error:
        return error
