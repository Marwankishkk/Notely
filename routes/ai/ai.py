from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.jwt import get_current_user
from core.rate_limit import rate_limit
from schemas.ai.ai import SummarizeRequest, SummarizeResponse
from schemas.notes.notes import NoteResponse
from services.AIService.ai import AIService

ai_router = APIRouter(prefix="/ai", tags=["ai"])


@ai_router.post(
    "/voice-note",
    response_model=NoteResponse,
    dependencies=[rate_limit("voice_note")],
)
async def create_voice_note(
    file: UploadFile = File(...),
    category_id: int | None = Form(default=None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AIService.create_note_from_voice(
        audio=file,
        user_id=current_user.id,
        db=db,
        category_id=category_id,
    )


@ai_router.post(
    "/summarize",
    response_model=SummarizeResponse,
    dependencies=[rate_limit("summarize")],
)
async def summarize_category_notes(
    data: SummarizeRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AIService.summarize_category_notes(
        category_id=data.category_id,
        user_id=current_user.id,
        db=db,
    )
