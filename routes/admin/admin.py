from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.admin import get_current_admin
from core.database import get_db
from schemas.admin.admin import (
    AdminStatsResponse,
    AdminUpdatePlanRequest,
    AdminUpdateUserRequest,
    AdminUserListResponse,
    AdminUserResponse,
)
from services.AdminService.admin import AdminService

admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/stats", response_model=AdminStatsResponse)
async def admin_stats(
    _admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService.get_stats(db)


@admin_router.get("/users", response_model=AdminUserListResponse)
async def admin_list_users(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService.list_users(db, q=q, limit=limit, offset=offset)


@admin_router.patch("/users/{user_id}/plan", response_model=AdminUserResponse)
async def admin_update_plan(
    user_id: int,
    data: AdminUpdatePlanRequest,
    _admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService.update_user_plan(db, user_id, data)


@admin_router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def admin_update_user(
    user_id: int,
    data: AdminUpdateUserRequest,
    _admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService.update_user(db, user_id, data)
