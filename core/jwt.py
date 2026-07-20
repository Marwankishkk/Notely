from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status, Depends, Request
from jose import JWTError, jwt

from core.config import settings
from core.cookies import ACCESS_COOKIE
from core.database import get_db
from core.token_blacklist import is_token_revoked
from repositories.user_repository.user_repository import UserRepository

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

REFRESH_TOKEN_EXPIRE_DAYS = 7
EMAIL_VERIFICATION_EXPIRE_HOURS = 24
PASSWORD_RESET_EXPIRE_HOURS = 1


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
    )


async def get_current_user(
    request: Request,
    db=Depends(get_db),
):
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise _unauthorized("Not authenticated")

    payload = verify_token(token)

    user = await UserRepository.find_by_id(
        db,
        int(payload["sub"]),
    )

    if user is None:
        raise _unauthorized("Invalid authentication credentials")

    if not user.is_active:
        raise _unauthorized("Account is not active")

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    to_encode["type"] = "access"

    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode["exp"] = expire

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["type"] = "refresh"
    to_encode["jti"] = str(uuid4())

    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode["exp"] = expire

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verify_token(token: str, token_type: str = "access") -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        if payload.get("type") != token_type:
            raise _unauthorized("Invalid token type")

        return payload

    except JWTError:
        raise _unauthorized("Invalid or expired token")


async def verify_refresh_token(token: str) -> dict:
    payload = verify_token(token, token_type="refresh")
    jti = payload.get("jti")
    if not jti or await is_token_revoked(jti):
        raise _unauthorized("Invalid or revoked refresh token")
    return payload


def create_email_verification_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["type"] = "email_verification"

    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode["exp"] = expire

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_password_reset_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["type"] = "password_reset"

    expire = datetime.now(timezone.utc) + timedelta(
        hours=PASSWORD_RESET_EXPIRE_HOURS
    )
    to_encode["exp"] = expire

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
