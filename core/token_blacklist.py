from datetime import datetime, timezone

from jose import JWTError, jwt

from core.config import settings
from core.rate_limit import get_redis

REFRESH_TOKEN_EXPIRE_DAYS = 7


async def revoke_refresh_token(token: str) -> None:
    """Blacklist a refresh token jti until its natural expiry."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        return

    if payload.get("type") != "refresh":
        return

    jti = payload.get("jti")
    if not jti:
        return

    exp = payload.get("exp")
    now = int(datetime.now(timezone.utc).timestamp())
    ttl = max(int(exp) - now, 1) if exp else REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600

    redis = get_redis()
    await redis.setex(f"revoked_refresh:{jti}", ttl, "1")


async def is_token_revoked(jti: str) -> bool:
    redis = get_redis()
    return bool(await redis.exists(f"revoked_refresh:{jti}"))
