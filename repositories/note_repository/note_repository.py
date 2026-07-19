from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models.notes.notes import Note


class NoteRepository:
    @staticmethod
    async def create_note(
        db: AsyncSession,
        title: str,
        content: str,
        user_id: int,
        category_id: int | None = None,
    ):
        db_note = Note(
            title=title,
            content=content,
            user_id=user_id,
            category_id=category_id,
        )
        db.add(db_note)
        await db.commit()
        await db.refresh(db_note)
        return db_note

    @staticmethod
    async def find_by_id(db: AsyncSession, note_id: int):
        result = await db.execute(
            select(Note).where(Note.id == note_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def find_all_by_user(
        db: AsyncSession,
        user_id: int,
        category_id: int | None = None,
    ):
        query = select(Note).where(Note.user_id == user_id)

        if category_id is not None:
            query = query.where(Note.category_id == category_id)

        query = query.order_by(Note.updated_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_note(
        db: AsyncSession,
        note: Note,
        title: str | None = None,
        content: str | None = None,
        category_id: int | None = None,
        update_category: bool = False,
    ):
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if update_category:
            note.category_id = category_id

        await db.commit()
        await db.refresh(note)
        return note

    @staticmethod
    async def delete_note(db: AsyncSession, note_id: int):
        await db.execute(
            delete(Note).where(Note.id == note_id)
        )
        await db.commit()

    @staticmethod
    async def get_category_notes(db: AsyncSession, category_id: int):
        query = select(Note).where(Note.category_id == category_id)
        result = await db.execute(query)
        return result.scalars().all()