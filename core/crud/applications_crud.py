from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.application import Application
from core.database.models.user import User
from core.enums import ApplicationStatus, UserRole


async def get_pending_applications(session: AsyncSession) -> list[Application]:
    result = await session.execute(
        select(Application)
        .where(Application.status == ApplicationStatus.PENDING)
        .options(selectinload(Application.applicant))
        .order_by(Application.created_at)
    )
    return list(result.scalars().all())


async def get_application_by_id(session: AsyncSession, application_id: int) -> Application | None:
    result = await session.execute(
        select(Application)
        .where(Application.id == application_id)
        .options(selectinload(Application.applicant))
    )
    return result.scalar_one_or_none()


async def get_all_admins(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User).where(User.role.in_([UserRole.ADMIN, UserRole.SUPERADMIN]))
    )
    return list(result.scalars().all())

async def get_resolved_applications(session: AsyncSession) -> list[Application]:
    result = await session.execute(
        select(Application)
        .where(Application.status != ApplicationStatus.PENDING)
        .options(selectinload(Application.applicant))
        .order_by(Application.reviewed_at.desc())
    )
    return list(result.scalars().all())