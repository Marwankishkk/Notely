from fastapi import HTTPException, status

from repositories.category_repository.category_repository import CategoryRepository
from schemas.categories.categories import CategoryCreate, CategoryUpdate


class CategoryService:

    @staticmethod
    async def create_category(category: CategoryCreate, user_id: int, db):
        return await CategoryRepository.create_category(
            db=db,
            name=category.name,
            user_id=user_id,
        )

    @staticmethod
    async def get_categories(user_id: int, db):
        return await CategoryRepository.find_all_by_user(db, user_id)

    @staticmethod
    async def get_category(category_id: int, user_id: int, db):
        category = await CategoryRepository.find_by_id(db, category_id)

        if category is None or category.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        return category

    @staticmethod
    async def update_category(
        category_id: int,
        data: CategoryUpdate,
        user_id: int,
        db,
    ):
        category = await CategoryService.get_category(category_id, user_id, db)

        return await CategoryRepository.update_category(db, category, data.name)

    @staticmethod
    async def delete_category(category_id: int, user_id: int, db):
        category = await CategoryService.get_category(category_id, user_id, db)

        await CategoryRepository.delete_category(db, category.id)

        return {
            "message": "Category deleted successfully."
        }
