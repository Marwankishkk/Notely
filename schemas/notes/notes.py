from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    title: str
    content: str
    category_id: int | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category_id: int | None = None


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    user_id: int
    category_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
