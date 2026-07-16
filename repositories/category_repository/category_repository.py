from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models.categories.categories import Category


class CategoryRepository:
    @staticmethod
    async def create_category(db: AsyncSession, name: str, user_id: int):
        db_category = Category(
            name=name,
            user_id=user_id,
        )
        db.add(db_category)
        await db.commit()
        await db.refresh(db_category)
        return db_category

    @staticmethod
    async def find_by_id(db: AsyncSession, category_id: int):
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def find_all_by_user(db: AsyncSession, user_id: int):
        result = await db.execute(
            select(Category).where(Category.user_id == user_id)
        )

        return result.scalars().all()

    @staticmethod
    async def update_category(db: AsyncSession, category: Category, name: str):
        category.name = name
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete_category(db: AsyncSession, category_id: int):
        await db.execute(
            delete(Category).where(Category.id == category_id)
        )
        await db.commit()
