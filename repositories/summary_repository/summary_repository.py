from datetime import datetime, UTC

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models.summaries.summaries import Summary


class SummaryRepository:
    @staticmethod
    async def find_by_id(db: AsyncSession, summary_id: int):
        result = await db.execute(
            select(Summary).where(Summary.id == summary_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_by_category_id(db: AsyncSession, category_id: int):
        result = await db.execute(
            select(Summary).where(Summary.category_id == category_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_all_by_user(db: AsyncSession, user_id: int):
        result = await db.execute(
            select(Summary)
            .where(Summary.user_id == user_id)
            .order_by(Summary.updated_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def upsert_summary(
        db: AsyncSession,
        user_id: int,
        category_id: int,
        summary_text: str,
    ):
        existing = await SummaryRepository.find_by_category_id(db, category_id)

        if existing is not None:
            existing.summary = summary_text
            existing.updated_at = datetime.now(UTC)
            await db.commit()
            await db.refresh(existing)
            return existing

        db_summary = Summary(
            summary=summary_text,
            user_id=user_id,
            category_id=category_id,
        )
        db.add(db_summary)
        await db.commit()
        await db.refresh(db_summary)
        return db_summary

    @staticmethod
    async def delete_summary(db: AsyncSession, summary_id: int):
        await db.execute(
            delete(Summary).where(Summary.id == summary_id)
        )
        await db.commit()
