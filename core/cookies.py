from fastapi import Response

from core.config import settings

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
REFRESH_TOKEN_EXPIRE_DAYS = 7


def _cookie_common() -> dict:
    samesite = settings.COOKIE_SAMESITE.lower()
    secure = settings.cookie_secure
    # Browsers require Secure when SameSite=None
    if samesite == "none":
        secure = True

    options: dict = {
        "httponly": True,
        "secure": secure,
        "samesite": samesite,
        "path": "/",
    }
    if settings.COOKIE_DOMAIN:
        options["domain"] = settings.COOKIE_DOMAIN
    return options


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    common = _cookie_common()

    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **common,
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        **common,
    )


def set_access_cookie(response: Response, access_token: str) -> None:
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **_cookie_common(),
    )


def clear_auth_cookies(response: Response) -> None:
    common = _cookie_common()
    for key in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(
            key=key,
            path=common["path"],
            domain=common.get("domain"),
            secure=common["secure"],
            httponly=True,
            samesite=common["samesite"],
        )
