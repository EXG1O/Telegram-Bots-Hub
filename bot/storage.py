from core.redis import redis

from typing import Any, overload
import json


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
        raw_data: str | None = await redis.get(self.redis_key)
        data: Any = json.loads(raw_data) if raw_data else {}

        if not isinstance(data, dict):
            raise ValueError("The entry in 'redis' must be of type 'dict'.")

        return data

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
        await redis.set(self.redis_key, json.dumps(data))
        return value

    async def set(self, key: str, value: Any) -> None:
        data: dict[str, Any] = await self.get_data()
        data[key] = value
        await redis.set(self.redis_key, json.dumps(data))

    async def delete(self, key: str) -> None:
        data: dict[str, Any] = await self.get_data()
        del data[key]
        await redis.set(self.redis_key, json.dumps(data))


class EventStorage:
    def __init__(self, bot_id: int, chat_id: int | None, user_id: int | None) -> None:
        self.chat = Storage(bot_id=bot_id, chat_id=chat_id) if chat_id else None
        self.user = (
            Storage(bot_id=bot_id, chat_id=chat_id, user_id=user_id)
            if chat_id and user_id
            else None
        )
