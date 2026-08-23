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

async def get_leaf_categories(session: AsyncSession) -> list[Category]:
    result = await session.execute(select(Category).order_by(Category.id))
    all_categories = list(result.scalars().all())

    parent_ids = {c.parent_id for c in all_categories if c.parent_id is not None}
    return [c for c in all_categories if c.id not in parent_ids]