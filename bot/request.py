from telegram.error import RetryAfter
from telegram.request import HTTPXRequest

from typing import Any
import asyncio


class ResilientHTTPXRequest(HTTPXRequest):
    async def _request_wrapper(self, *args: Any, **kwargs: Any) -> bytes:
        try:
            return await super()._request_wrapper(*args, **kwargs)
        except RetryAfter as error:
            await asyncio.sleep(error.retry_after)
            return await self._request_wrapper(*args, **kwargs)
