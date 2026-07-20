from datetime import datetime, UTC, date
from enum import Enum

from sqlalchemy import (
    DateTime,
    Date,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Plan(str, Enum):
    BASIC = "basic"
    PRO = "pro"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INACTIVE = "inactive"


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_subscriptions_user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    plan: Mapped[str] = mapped_column(
        String,
        default=Plan.BASIC.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String,
        default=SubscriptionStatus.ACTIVE.value,
        nullable=False,
    )

    # Provider-agnostic payment refs (Paymob, Fawry, etc. later).
    payment_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    external_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    external_subscription_id: Mapped[str | None] = mapped_column(String, nullable=True)

    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Tracks summarize API calls per calendar day (UTC).
    summary_usage_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    summaries_used_today: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
