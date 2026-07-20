from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.jwt import get_current_user
from core.rate_limit import rate_limit
from schemas.users.users import UserCreate, UserResponse, UserLogin, RefreshTokenRequest
from services.UserService.users import UserService

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post("/register", dependencies=[rate_limit("register")])
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.register_user(user, db)


@user_router.post("/login", dependencies=[rate_limit("login")])
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    return await UserService.login_user(user, db)


@user_router.get("/verify-email", dependencies=[rate_limit("verify_email")])
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.verify_email(token, db)


@user_router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user=Depends(get_current_user),
):
    return await UserService.get_me(current_user)


@user_router.post("/refresh", dependencies=[rate_limit("refresh")])
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.refresh_access_token(
        request.refresh_token,
        db,
    )


@user_router.post("/logout")
async def logout():
    return {
        "message": "Logged out successfully."
    }
