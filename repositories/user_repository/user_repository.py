from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,delete

from models.users.users import User

class UserRepository():
    @staticmethod
    async def create_user(db: AsyncSession, user):
        db_user = User(
            name=user.name,
            email=user.email,
            password=user.password,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    @staticmethod
    async def find_by_email(
        db: AsyncSession,
        email: str
    ):
        result = await db.execute(
            select(User).where(User.email == email)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def find_by_id(db, user_id: int):
        result = await db.execute(
            select(User).where(User.id == user_id)
        )

        return result.scalar_one_or_none()


    @staticmethod
    async def delete_user(db, user_id: int):
        await db.execute(
            delete(User).where(User.id == user_id)
        )
        await db.commit()