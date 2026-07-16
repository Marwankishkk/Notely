from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.jwt import get_current_user
from schemas.categories.categories import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from services.CategoryService.categories import CategoryService

category_router = APIRouter(prefix="/categories", tags=["categories"])


@category_router.post("/", response_model=CategoryResponse)
async def create_category(
    category: CategoryCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CategoryService.create_category(
        category,
        current_user.id,
        db,
    )


@category_router.get("/", response_model=list[CategoryResponse])
async def get_categories(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CategoryService.get_categories(current_user.id, db)


@category_router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CategoryService.get_category(
        category_id,
        current_user.id,
        db,
    )


@category_router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CategoryService.update_category(
        category_id,
        data,
        current_user.id,
        db,
    )


@category_router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CategoryService.delete_category(
        category_id,
        current_user.id,
        db,
    )
