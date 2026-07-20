from datetime import datetime, UTC

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.notes.notes import Note
from models.subscriptions.subscriptions import Plan, Subscription, SubscriptionStatus
from models.summaries.summaries import Summary
from models.users.users import User
from repositories.subscription_repository.subscription_repository import (
    SubscriptionRepository,
)
from repositories.user_repository.user_repository import UserRepository
from schemas.admin.admin import (
    AdminStatsResponse,
    AdminUpdatePlanRequest,
    AdminUpdateUserRequest,
    AdminUserListResponse,
    AdminUserResponse,
)
from services.SubscriptionService.subscriptions import SubscriptionService


class AdminService:
    @staticmethod
    async def get_stats(db: AsyncSession) -> AdminStatsResponse:
        total_users = await db.scalar(select(func.count()).select_from(User)) or 0
        active_users = (
            await db.scalar(
                select(func.count()).select_from(User).where(User.is_active.is_(True))
            )
            or 0
        )
        notes_total = await db.scalar(select(func.count()).select_from(Note)) or 0
        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        notes_today = (
            await db.scalar(
                select(func.count())
                .select_from(Note)
                .where(Note.created_at >= today_start)
            )
            or 0
        )
        summaries_total = (
            await db.scalar(select(func.count()).select_from(Summary)) or 0
        )
        plan_basic = (
            await db.scalar(
                select(func.count())
                .select_from(Subscription)
                .where(Subscription.plan == Plan.BASIC.value)
            )
            or 0
        )
        plan_pro = (
            await db.scalar(
                select(func.count())
                .select_from(Subscription)
                .where(Subscription.plan == Plan.PRO.value)
            )
            or 0
        )

        return AdminStatsResponse(
            total_users=total_users,
            active_users=active_users,
            notes_total=notes_total,
            notes_today=notes_today,
            summaries_total=summaries_total,
            plan_basic=plan_basic,
            plan_pro=plan_pro,
        )

    @staticmethod
    async def list_users(
        db: AsyncSession,
        *,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AdminUserListResponse:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        filters = []
        if q and q.strip():
            term = f"%{q.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(User.email).like(term),
                    func.lower(User.name).like(term),
                )
            )

        count_stmt = select(func.count()).select_from(User)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = await db.scalar(count_stmt) or 0

        notes_count = (
            select(func.count())
            .where(Note.user_id == User.id)
            .correlate(User)
            .scalar_subquery()
            .label("notes_count")
        )
        summaries_count = (
            select(func.count())
            .where(Summary.user_id == User.id)
            .correlate(User)
            .scalar_subquery()
            .label("summaries_count")
        )
        last_note_at = (
            select(func.max(Note.created_at))
            .where(Note.user_id == User.id)
            .correlate(User)
            .scalar_subquery()
            .label("last_note_at")
        )

        stmt = (
            select(
                User,
                Subscription.plan,
                Subscription.status,
                notes_count,
                summaries_count,
                last_note_at,
            )
            .outerjoin(Subscription, Subscription.user_id == User.id)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if filters:
            stmt = stmt.where(*filters)

        rows = (await db.execute(stmt)).all()
        items = [
            AdminUserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                is_active=user.is_active,
                created_at=user.created_at,
                plan=plan or Plan.BASIC.value,
                subscription_status=sub_status or SubscriptionStatus.INACTIVE.value,
                notes_count=int(n_count or 0),
                summaries_count=int(s_count or 0),
                last_note_at=last_at,
            )
            for user, plan, sub_status, n_count, s_count, last_at in rows
        ]

        return AdminUserListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    async def update_user_plan(
        db: AsyncSession,
        user_id: int,
        data: AdminUpdatePlanRequest,
    ) -> AdminUserResponse:
        user = await UserRepository.find_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        subscription = await SubscriptionService.get_or_create_for_user(user_id, db)
        await SubscriptionRepository.update_subscription(
            db,
            subscription,
            plan=data.plan.value,
            status=SubscriptionStatus.ACTIVE.value,
        )

        return await AdminService._user_row(db, user_id)

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: int,
        data: AdminUpdateUserRequest,
    ) -> AdminUserResponse:
        user = await UserRepository.find_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.is_active = data.is_active
        user.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(user)

        return await AdminService._user_row(db, user_id)

    @staticmethod
    async def _user_row(db: AsyncSession, user_id: int) -> AdminUserResponse:
        notes_count = (
            select(func.count())
            .where(Note.user_id == User.id)
            .correlate(User)
            .scalar_subquery()
            .label("notes_count")
        )
        summaries_count = (
            select(func.count())
            .where(Summary.user_id == User.id)
            .correlate(User)
            .scalar_subquery()
            .label("summaries_count")
        )
        last_note_at = (
            select(func.max(Note.created_at))
            .where(Note.user_id == User.id)
            .correlate(User)
            .scalar_subquery()
            .label("last_note_at")
        )
        stmt = (
            select(
                User,
                Subscription.plan,
                Subscription.status,
                notes_count,
                summaries_count,
                last_note_at,
            )
            .outerjoin(Subscription, Subscription.user_id == User.id)
            .where(User.id == user_id)
        )
        row = (await db.execute(stmt)).one_or_none()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        user, plan, sub_status, n_count, s_count, last_at = row
        return AdminUserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            created_at=user.created_at,
            plan=plan or Plan.BASIC.value,
            subscription_status=sub_status or SubscriptionStatus.INACTIVE.value,
            notes_count=int(n_count or 0),
            summaries_count=int(s_count or 0),
            last_note_at=last_at,
        )
