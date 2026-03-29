import msgspec

from core.msgspec import json_encoder
from core.redis import redis

from .models import BotStorageData, ChatStorageData, UserStorageData

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
import asyncio
import weakref

bot_storage_decoder = msgspec.json.Decoder(BotStorageData)
chat_storage_decoder = msgspec.json.Decoder(ChatStorageData)
user_storage_decoder = msgspec.json.Decoder(UserStorageData)

_storage_main_lock = asyncio.Lock()
_storage_locks: weakref.WeakValueDictionary[str, asyncio.Lock] = (
    weakref.WeakValueDictionary()
)


class Storage[T: msgspec.Struct]:
    def __init__(
        self,
        *,
        bot_id: int,
        default_factory: Callable[[], T],
        decoder: msgspec.json.Decoder[T],
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> None:
        self.default_factory = default_factory
        self.decoder = decoder

        key_parts: list[str] = ['tbh', str(bot_id)]

        if chat_id is not None:
            key_parts.append(str(chat_id))
        if user_id is not None:
            key_parts.append(str(user_id))

        self.redis_key = ':'.join(key_parts)

    @classmethod
    def for_bot(cls, bot_id: int) -> Storage[BotStorageData]:
        return Storage(
            bot_id=bot_id, default_factory=BotStorageData, decoder=bot_storage_decoder
        )

    @classmethod
    def for_chat(cls, bot_id: int, chat_id: int) -> Storage[ChatStorageData]:
        return Storage(
            bot_id=bot_id,
            chat_id=chat_id,
            default_factory=ChatStorageData,
            decoder=chat_storage_decoder,
        )

    @classmethod
    def for_user(
        cls, bot_id: int, chat_id: int, user_id: int
    ) -> Storage[UserStorageData]:
        return Storage(
            bot_id=bot_id,
            chat_id=chat_id,
            user_id=user_id,
            default_factory=UserStorageData,
            decoder=user_storage_decoder,
        )

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[T]:
        key: str = self.redis_key

        async with _storage_main_lock:
            lock: asyncio.Lock | None = _storage_locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                _storage_locks[key] = lock

        async with lock:
            data: T = await self.get_data()
            yield data
            await self._set_data(data)

    async def get_data(self) -> T:
        response: bytes | None = await redis.get(self.redis_key)

        if not response:
            return self.default_factory()

        try:
            return self.decoder.decode(response)
        except msgspec.DecodeError:
            return self.default_factory()

    async def _set_data(self, data: T) -> None:
        await redis.set(self.redis_key, json_encoder.encode(data))
