import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


# Rate limiting: max `limit` calls per `window` seconds per key
async def check_rate_limit(redis: aioredis.Redis, key: str, limit: int, window: int) -> bool:
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, window)
    return current <= limit
