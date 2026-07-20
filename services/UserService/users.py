from fastapi import HTTPException, status

from schemas.users.users import (
    UserCreate,
    UserLogin,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from core.security import hash_password, verify_password
from core.jwt import (
    create_access_token,
    create_refresh_token,
    create_email_verification_token,
    create_password_reset_token,
    verify_token,
    verify_refresh_token,
)
from core.token_blacklist import revoke_refresh_token
from repositories.user_repository.user_repository import UserRepository
from repositories.subscription_repository.subscription_repository import (
    SubscriptionRepository,
)
from services.email_service import EmailService
from services.SubscriptionService.subscriptions import SubscriptionService
from core.plans import get_plan_limits
from schemas.subscriptions.subscriptions import (
    MeResponse,
    PlanLimitsResponse,
    SubscriptionResponse,
    UsageTodayResponse,
)


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

        await SubscriptionRepository.create_basic_subscription(
            db,
            created_user.id,
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
    async def forgot_password(data: ForgotPasswordRequest, db):
        email = data.email.lower()
        user = await UserRepository.find_by_email(db, email)

        # Always return the same message to avoid email enumeration.
        generic_response = {
            "message": (
                "If an account with that email exists, "
                "a password reset link has been sent."
            )
        }

        if user is None:
            return generic_response

        reset_token = create_password_reset_token(
            {
                "sub": str(user.id),
                "email": user.email,
            }
        )

        try:
            EmailService.send_password_reset_email(user.email, reset_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email. Please try again.",
            )

        return generic_response

    @staticmethod
    async def reset_password(data: ResetPasswordRequest, db):
        payload = verify_token(
            data.token,
            token_type="password_reset",
        )

        user = await UserRepository.find_by_id(
            db,
            int(payload["sub"]),
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        if payload.get("email") and payload["email"] != user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user.password = hash_password(data.new_password)
        await db.commit()

        return {
            "message": "Password reset successfully. You can now log in."
        }

    @staticmethod
    async def get_me(current_user, db):
        subscription = await SubscriptionService.get_or_create_for_user(
            current_user.id,
            db,
        )
        plan = SubscriptionService.effective_plan(subscription)
        limits = get_plan_limits(plan)
        usage = await SubscriptionService.get_usage_today(current_user.id, db)

        return MeResponse(
            id=current_user.id,
            name=current_user.name,
            email=current_user.email,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            subscription=SubscriptionResponse.model_validate(subscription),
            limits=PlanLimitsResponse(
                notes_per_day=limits.notes_per_day,
                max_audio_seconds=limits.max_audio_seconds,
                summaries_per_day=limits.summaries_per_day,
            ),
            usage_today=UsageTodayResponse(
                notes=usage["notes"],
                summaries=usage["summaries"],
            ),
        )

    @staticmethod
    async def refresh_access_token(refresh_token: str, db):
        payload = await verify_refresh_token(refresh_token)

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

        # Rotate refresh token: revoke the old one.
        await revoke_refresh_token(refresh_token)

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
        }

        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
        }

    @staticmethod
    async def logout(refresh_token: str | None):
        if refresh_token:
            await revoke_refresh_token(refresh_token)
        return {
            "message": "Logged out successfully."
        }
