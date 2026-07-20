from datetime import datetime, UTC, date

from fastapi import HTTPException, status
from sqlalchemy import func, select

from core.plans import get_plan_limits
from models.notes.notes import Note
from models.subscriptions.subscriptions import Plan, SubscriptionStatus
from repositories.subscription_repository.subscription_repository import (
    SubscriptionRepository,
)


class SubscriptionService:

    @staticmethod
    async def get_or_create_for_user(user_id: int, db):
        subscription = await SubscriptionRepository.find_by_user_id(db, user_id)
        if subscription is None:
            subscription = await SubscriptionRepository.create_basic_subscription(
                db, user_id
            )
        return subscription

    @staticmethod
    def is_pro(subscription) -> bool:
        if subscription is None:
            return False

        if subscription.plan != Plan.PRO.value:
            return False

        if subscription.status not in (
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.TRIALING.value,
        ):
            return False

        if subscription.current_period_end is not None:
            end = subscription.current_period_end
            if end.tzinfo is None:
                end = end.replace(tzinfo=UTC)
            if end < datetime.now(UTC):
                return False

        return True

    @staticmethod
    def effective_plan(subscription) -> str:
        if SubscriptionService.is_pro(subscription):
            return Plan.PRO.value
        return Plan.BASIC.value

    @staticmethod
    def _today() -> date:
        return datetime.now(UTC).date()

    @staticmethod
    def summaries_used_today(subscription) -> int:
        today = SubscriptionService._today()
        if subscription.summary_usage_date != today:
            return 0
        return subscription.summaries_used_today or 0

    @staticmethod
    async def get_usage_today(user_id: int, db) -> dict[str, int]:
        start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        subscription = await SubscriptionService.get_or_create_for_user(user_id, db)

        notes_result = await db.execute(
            select(func.count())
            .select_from(Note)
            .where(Note.user_id == user_id, Note.created_at >= start)
        )

        return {
            "notes": int(notes_result.scalar_one()),
            "summaries": SubscriptionService.summaries_used_today(subscription),
        }

    @staticmethod
    async def assert_can_create_voice_note(
        user_id: int,
        db,
        duration_seconds: float | None = None,
    ):
        subscription = await SubscriptionService.get_or_create_for_user(user_id, db)
        plan = SubscriptionService.effective_plan(subscription)
        limits = get_plan_limits(plan)
        usage = await SubscriptionService.get_usage_today(user_id, db)

        if (
            limits.notes_per_day is not None
            and usage["notes"] >= limits.notes_per_day
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Daily note limit reached ({limits.notes_per_day}/day "
                    f"on {plan} plan). Upgrade to Pro for a higher limit."
                ),
            )

        if limits.max_audio_seconds is not None:
            if duration_seconds is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not determine audio duration.",
                )
            if duration_seconds > limits.max_audio_seconds:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        f"Audio exceeds the {limits.max_audio_seconds}s limit "
                        f"for the {plan} plan."
                    ),
                )

    @staticmethod
    async def assert_can_summarize(user_id: int, db):
        subscription = await SubscriptionService.get_or_create_for_user(user_id, db)
        plan = SubscriptionService.effective_plan(subscription)
        limits = get_plan_limits(plan)
        used = SubscriptionService.summaries_used_today(subscription)

        if limits.summaries_per_day is not None and used >= limits.summaries_per_day:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Daily summary limit reached ({limits.summaries_per_day}/day "
                    f"on {plan} plan). Upgrade to Pro for a higher limit."
                ),
            )

    @staticmethod
    async def record_summary_usage(user_id: int, db):
        subscription = await SubscriptionService.get_or_create_for_user(user_id, db)
        today = SubscriptionService._today()

        if subscription.summary_usage_date != today:
            subscription.summary_usage_date = today
            subscription.summaries_used_today = 1
        else:
            subscription.summaries_used_today = (
                subscription.summaries_used_today or 0
            ) + 1

        subscription.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(subscription)
        return subscription
