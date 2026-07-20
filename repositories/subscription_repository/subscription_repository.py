from datetime import datetime, UTC

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.subscriptions.subscriptions import (
    Plan,
    Subscription,
    SubscriptionStatus,
)


class SubscriptionRepository:
    @staticmethod
    async def create_basic_subscription(db: AsyncSession, user_id: int):
        subscription = Subscription(
            user_id=user_id,
            plan=Plan.BASIC.value,
            status=SubscriptionStatus.ACTIVE.value,
            cancel_at_period_end=False,
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription

    @staticmethod
    async def find_by_user_id(db: AsyncSession, user_id: int):
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_by_external_customer_id(db: AsyncSession, customer_id: str):
        result = await db.execute(
            select(Subscription).where(
                Subscription.external_customer_id == customer_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_by_external_subscription_id(
        db: AsyncSession,
        external_subscription_id: str,
    ):
        result = await db.execute(
            select(Subscription).where(
                Subscription.external_subscription_id == external_subscription_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_subscription(
        db: AsyncSession,
        subscription: Subscription,
        *,
        plan: str,
        status: str,
        payment_provider: str | None = None,
        external_customer_id: str | None = None,
        external_subscription_id: str | None = None,
        current_period_end: datetime | None = None,
        cancel_at_period_end: bool | None = None,
    ):
        subscription.plan = plan
        subscription.status = status
        if payment_provider is not None:
            subscription.payment_provider = payment_provider
        if external_customer_id is not None:
            subscription.external_customer_id = external_customer_id
        if external_subscription_id is not None:
            subscription.external_subscription_id = external_subscription_id
        if current_period_end is not None:
            subscription.current_period_end = current_period_end
        if cancel_at_period_end is not None:
            subscription.cancel_at_period_end = cancel_at_period_end
        subscription.updated_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(subscription)
        return subscription
