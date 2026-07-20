from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SummaryCreate(BaseModel):
    summary: str
    category_id: int


class SummaryUpdate(BaseModel):
    summary: str | None = None


class SummaryResponse(BaseModel):
    id: int
    summary: str
    user_id: int
    category_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
