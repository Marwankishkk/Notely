from fastapi import HTTPException,status

from repositories.user_repository import user_repository
from schemas.users.users import UserCreate,UserLogin
from core.security import hash_password,verify_password
from core.jwt import create_access_token,create_refresh_token,create_email_verification_token,verify_token
from repositories.user_repository.user_repository import UserRepository
from services.email_service import EmailService

class UserService:

    @staticmethod
    async def register_user(user: UserCreate, db):
        user.email = user.email.lower()

        existing_email = await UserRepository.find_by_email(db, user.email)

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user.password = hash_password(user.password)

        created_user = await UserRepository.create_user(
            db=db,
            user=user,
        )

        verification_token = create_email_verification_token(
            {
                "sub": str(created_user.id),
                "email": created_user.email,
            }
        )

        try:
            EmailService.send_verification_email(
                created_user.email,
                verification_token,
            )
        except Exception:
            await UserRepository.delete_user(db, created_user.id)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email. Please try again.",
            )

        return {
            "message": "Registration successful. Please check your email to verify your account."
        }
    @staticmethod
    async def login_user(user: UserLogin, db):
        user.email = user.email.lower()
        existing_user = await UserRepository.find_by_email(db, user.email)

        if existing_user is None or existing_user.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )


        if not verify_password(user.password, existing_user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        token_data = {
            "sub": str(existing_user.id),
            "email": existing_user.email,
            "name": existing_user.name,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    async def verify_email(token: str, db):
        payload = verify_token(
            token,
            token_type="email_verification",
        )

        user = await UserRepository.find_by_id(
            db,
            int(payload["sub"]),
        )

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        if user.is_active:
            return {
                "message": "Email already verified."
            }

        user.is_active = True

        await db.commit()

        return {
            "message": "Email verified successfully."
        }

    @staticmethod
    async def get_me(current_user):
        return current_user

    @staticmethod
    async def refresh_access_token(refresh_token: str, db):
        payload = verify_token(
            refresh_token,
            token_type="refresh",
        )

        user = await UserRepository.find_by_id(
            db,
            int(payload["sub"]),
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive",
            )

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
        }

        access_token = create_access_token(token_data)

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }