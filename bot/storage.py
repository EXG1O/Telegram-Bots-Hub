import msgspec

from core.msgspec import json_encoder
from core.redis import redis

from typing import Any, overload

storage_decoder = msgspec.json.Decoder(dict[str, Any])


class Storage:
    def __init__(
        self, *, bot_id: int, chat_id: int | None = None, user_id: int | None = None
    ) -> None:
        key_parts: list[str] = ['tbh', str(bot_id)]

        if chat_id is not None:
            key_parts.append(str(chat_id))
        if user_id is not None:
            key_parts.append(str(user_id))

        self.redis_key = ':'.join(key_parts)

    async def get_data(self) -> dict[str, Any]:
        data: bytes | None = await redis.get(self.redis_key)
        return storage_decoder.decode(data) if data else {}

    @overload
    async def get(self, key: str, default_value: None = None) -> Any | None: ...
    @overload
    async def get[T](self, key: str, default_value: T) -> Any | T: ...
    async def get(self, key: str, default_value: Any | None = None) -> Any | None:
        return (await self.get_data()).get(key, default_value)

    @overload
    async def pop(self, key: str, default_value: None = None) -> Any | None: ...
    @overload
    async def pop[T](self, key: str, default_value: T) -> Any | T: ...
    async def pop(self, key: str, default_value: Any | None = None) -> Any | None:
        data: dict[str, Any] = await self.get_data()
        value: Any | None = data.pop(key, default_value)
        await redis.set(self.redis_key, json_encoder.encode(data))
        return value

    async def set(self, key: str, value: Any) -> None:
        data: dict[str, Any] = await self.get_data()
        data[key] = value
        await redis.set(self.redis_key, json_encoder.encode(data))

    async def delete(self, key: str) -> None:
        data: dict[str, Any] = await self.get_data()
        del data[key]
        await redis.set(self.redis_key, json_encoder.encode(data))
