from fastapi import Depends, HTTPException, status
from pyrate_limiter import Duration, Limiter, Rate, RedisBucket
from redis.asyncio import Redis
from starlette.requests import Request

from core.config import settings

_redis: Redis | None = None
_limiters: dict[str, Limiter] = {}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def _make_limiter(times: int, seconds: int, bucket_key: str) -> Limiter:
    assert _redis is not None
    rates = [Rate(times, Duration.SECOND * seconds)]
    bucket = await RedisBucket.init(rates, _redis, bucket_key)
    return Limiter(bucket)


async def init_rate_limiter() -> Redis:
    global _redis

    _redis = Redis.from_url(settings.REDIS_URL, decode_responses=False)
    await _redis.ping()

    _limiters.update(
        {
            "login": await _make_limiter(5, 60, "rl:login"),
            "register": await _make_limiter(3, 60, "rl:register"),
            "verify_email": await _make_limiter(10, 60, "rl:verify-email"),
            "refresh": await _make_limiter(20, 60, "rl:refresh"),
            "voice_note": await _make_limiter(10, 60, "rl:voice-note"),
            "summarize": await _make_limiter(1, 60, "rl:summarize"),
        }
    )

    return _redis


async def close_rate_limiter() -> None:
    global _redis
    _limiters.clear()
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def rate_limit(name: str):
    async def dependency(request: Request):
        limiter = _limiters.get(name)
        if limiter is None:
            return None

        key = f"{name}:{_client_ip(request)}"
        allowed = await limiter.try_acquire_async(key, blocking=False)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

    return Depends(dependency)
