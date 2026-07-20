from fastapi import HTTPException, status

from repositories.category_repository.category_repository import CategoryRepository
from repositories.summary_repository.summary_repository import SummaryRepository


class SummaryService:

    @staticmethod
    async def get_summaries(user_id: int, db):
        return await SummaryRepository.find_all_by_user(db, user_id)

    @staticmethod
    async def get_summary(summary_id: int, user_id: int, db):
        summary = await SummaryRepository.find_by_id(db, summary_id)

        if summary is None or summary.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summary not found",
            )

        return summary

    @staticmethod
    async def get_summary_by_category(category_id: int, user_id: int, db):
        category = await CategoryRepository.find_by_id(db, category_id)
        if category is None or category.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        summary = await SummaryRepository.find_by_category_id(db, category_id)
        if summary is None or summary.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summary not found",
            )

        return summary

    @staticmethod
    async def delete_summary(summary_id: int, user_id: int, db):
        summary = await SummaryService.get_summary(summary_id, user_id, db)
        await SummaryRepository.delete_summary(db, summary.id)

        return {
            "message": "Summary deleted successfully."
        }
