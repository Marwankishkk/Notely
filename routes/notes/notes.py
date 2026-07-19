from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.jwt import get_current_user
from schemas.notes.notes import NoteResponse, NoteUpdate
from services.NoteService.notes import NoteService

note_router = APIRouter(prefix="/notes", tags=["notes"])


@note_router.get("/", response_model=list[NoteResponse])
async def get_notes(
    category_id: int | None = Query(default=None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NoteService.get_notes(
        current_user.id,
        db,
        category_id=category_id,
    )


@note_router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NoteService.get_note(
        note_id,
        current_user.id,
        db,
    )


@note_router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    data: NoteUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NoteService.update_note(
        note_id,
        data,
        current_user.id,
        db,
    )


@note_router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NoteService.delete_note(
        note_id,
        current_user.id,
        db,
    )
