from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.category import Category


async def get_categories_by_parent(
    session: AsyncSession, parent_id: int | None
) -> list[Category]:
    result = await session.execute(
        select(Category)
        .where(Category.parent_id == parent_id, Category.is_active == True)
        .order_by(Category.id)
    )
    return list(result.scalars().all())


async def get_category_by_id(
    session: AsyncSession, category_id: int
) -> Category | None:
    result = await session.execute(
        select(Category).where(Category.id == category_id)
    )
    return result.scalar_one_or_none()