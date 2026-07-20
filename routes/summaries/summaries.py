from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.jwt import get_current_user
from schemas.summaries.summaries import SummaryResponse
from services.SummaryService.summaries import SummaryService

summary_router = APIRouter(prefix="/summaries", tags=["summaries"])


@summary_router.get("/", response_model=list[SummaryResponse])
async def get_summaries(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SummaryService.get_summaries(current_user.id, db)


@summary_router.get(
    "/category/{category_id}",
    response_model=SummaryResponse,
)
async def get_summary_by_category(
    category_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SummaryService.get_summary_by_category(
        category_id,
        current_user.id,
        db,
    )


@summary_router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(
    summary_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SummaryService.get_summary(
        summary_id,
        current_user.id,
        db,
    )


@summary_router.delete("/{summary_id}")
async def delete_summary(
    summary_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SummaryService.delete_summary(
        summary_id,
        current_user.id,
        db,
    )
