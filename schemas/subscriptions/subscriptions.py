from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan: str
    status: str
    payment_provider: str | None
    external_customer_id: str | None
    external_subscription_id: str | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlanLimitsResponse(BaseModel):
    notes_per_day: int | None
    max_audio_seconds: int | None
    summaries_per_day: int | None


class UsageTodayResponse(BaseModel):
    notes: int
    summaries: int


class MeResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: datetime
    subscription: SubscriptionResponse | None
    limits: PlanLimitsResponse
    usage_today: UsageTodayResponse

    model_config = ConfigDict(from_attributes=True)
