from fastapi import HTTPException, status

from repositories.category_repository.category_repository import CategoryRepository
from repositories.note_repository.note_repository import NoteRepository
from schemas.notes.notes import NoteUpdate


class NoteService:

    @staticmethod
    async def get_notes(user_id: int, db, category_id: int | None = None):
        if category_id is not None:
            category = await CategoryRepository.find_by_id(db, category_id)
            if category is None or category.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found",
                )

        return await NoteRepository.find_all_by_user(
            db,
            user_id,
            category_id=category_id,
        )

    @staticmethod
    async def get_note(note_id: int, user_id: int, db):
        note = await NoteRepository.find_by_id(db, note_id)

        if note is None or note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )

        return note

    @staticmethod
    async def update_note(note_id: int, data: NoteUpdate, user_id: int, db):
        note = await NoteService.get_note(note_id, user_id, db)
        updates = data.model_dump(exclude_unset=True)

        if "category_id" in updates and updates["category_id"] is not None:
            category = await CategoryRepository.find_by_id(
                db, updates["category_id"]
            )
            if category is None or category.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found",
                )

        return await NoteRepository.update_note(
            db=db,
            note=note,
            title=updates.get("title"),
            content=updates.get("content"),
            category_id=updates.get("category_id"),
            update_category="category_id" in updates,
        )

    @staticmethod
    async def delete_note(note_id: int, user_id: int, db):
        note = await NoteService.get_note(note_id, user_id, db)

        await NoteRepository.delete_note(db, note.id)

        return {
            "message": "Note deleted successfully."
        }
