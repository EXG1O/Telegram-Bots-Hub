from aiolimiter import AsyncLimiter
from cachetools import TTLCache

from core.settings import (
    TELEGRAM_GLOBAL_RATE_LIMIT,
    TELEGRAM_GLOBAL_RATE_PERIOD,
    TELEGRAM_GROUP_RATE_LIMIT,
    TELEGRAM_GROUP_RATE_PERIOD,
    TELEGRAM_USER_RATE_LIMIT,
    TELEGRAM_USER_RATE_PERIOD,
)

from typing import Final


class Limiter:
    _CACHE_MAXSIZE: Final[int] = 750
    _CACHE_TTL: Final[int] = 600

    def __init__(self) -> None:
        self._global_limiter = AsyncLimiter(
            max_rate=TELEGRAM_GLOBAL_RATE_LIMIT,
            time_period=TELEGRAM_GLOBAL_RATE_PERIOD,
        )
        self._user_limiters: TTLCache[int, AsyncLimiter] = TTLCache(
            maxsize=self._CACHE_MAXSIZE, ttl=self._CACHE_TTL
        )
        self._group_limiters: TTLCache[int, AsyncLimiter] = TTLCache(
            maxsize=self._CACHE_MAXSIZE, ttl=self._CACHE_TTL
        )

    def _get_or_create_limiter(
        self,
        cache: TTLCache[int, AsyncLimiter],
        chat_id: int,
        max_rate: float,
        time_period: float,
    ) -> AsyncLimiter:
        if chat_id not in cache:
            cache[chat_id] = AsyncLimiter(max_rate=max_rate, time_period=time_period)
        return cache[chat_id]

    def _get_chat_limiter(self, chat_id: int) -> AsyncLimiter:
        return (
            self._get_or_create_limiter(
                cache=self._user_limiters,
                chat_id=chat_id,
                max_rate=TELEGRAM_USER_RATE_LIMIT,
                time_period=TELEGRAM_USER_RATE_PERIOD,
            )
            if chat_id > 0
            else self._get_or_create_limiter(
                cache=self._group_limiters,
                chat_id=chat_id,
                max_rate=TELEGRAM_GROUP_RATE_LIMIT,
                time_period=TELEGRAM_GROUP_RATE_PERIOD,
            )
        )

    async def acquire(self, chat_id: int | None = None) -> None:
        if chat_id is not None:
            async with self._get_chat_limiter(chat_id), self._global_limiter:
                return

        async with self._global_limiter:
            return
