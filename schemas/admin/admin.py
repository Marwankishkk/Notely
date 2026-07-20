from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.subscriptions.subscriptions import Plan


class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    notes_total: int
    notes_today: int
    summaries_total: int
    plan_basic: int
    plan_pro: int


class AdminUserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    is_active: bool
    created_at: datetime
    plan: str
    subscription_status: str
    notes_count: int
    summaries_count: int
    last_note_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int
    limit: int
    offset: int


class AdminUpdatePlanRequest(BaseModel):
    plan: Plan


class AdminUpdateUserRequest(BaseModel):
    is_active: bool = Field(...)
