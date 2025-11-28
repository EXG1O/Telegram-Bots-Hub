from redis.asyncio import Redis

from .settings import REDIS_URL

redis: Redis = Redis.from_url(REDIS_URL, decode_responses=True)
