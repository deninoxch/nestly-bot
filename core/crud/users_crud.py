from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.user import User
from core.enums import UserRole


async def get_admins(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User).where(User.role == UserRole.ADMIN).order_by(User.id)
    )
    return list(result.scalars().all())


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def set_user_role(session: AsyncSession, user: User, role: UserRole) -> None:
    user.role = role
    await session.commit()