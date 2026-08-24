from sqlalchemy import select, distinct
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.product import Product
from core.enums import Country


async def get_products_by_category(
    session: AsyncSession, category_id: int
) -> list[Product]:
    result = await session.execute(
        select(Product)
        .where(Product.category_id == category_id, Product.is_active == True)
        .options(selectinload(Product.photos))
        .order_by(Product.id)
    )
    return list(result.scalars().all())


async def get_product_by_id(
    session: AsyncSession, product_id: int
) -> Product | None:
    result = await session.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(Product.photos))
    )
    return result.scalar_one_or_none()


async def get_distinct_countries(
    session: AsyncSession, category_id: int
) -> list[Country]:
    result = await session.execute(
        select(distinct(Product.country))
        .where(Product.category_id == category_id, Product.is_active == True)
    )
    return [row[0] for row in result.all()]


async def get_products_by_category_and_country(
    session: AsyncSession, category_id: int, country: Country
) -> list[Product]:
    result = await session.execute(
        select(Product)
        .where(
            Product.category_id == category_id,
            Product.country == country,
            Product.is_active == True,
        )
        .options(selectinload(Product.photos))
        .order_by(Product.id)
    )
    return list(result.scalars().all())

async def get_all_products_by_category(session: AsyncSession, category_id: int) -> list[Product]:
    result = await session.execute(
        select(Product)
        .where(Product.category_id == category_id)
        .options(selectinload(Product.photos))
        .order_by(Product.id)
    )
    return list(result.scalars().all())


async def toggle_product_active(session: AsyncSession, product: Product) -> None:
    product.is_active = not product.is_active
    await session.commit()


async def update_product_price(session: AsyncSession, product: Product, price) -> None:
    product.price = price
    await session.commit()

async def get_active_product_by_id(session: AsyncSession, product_id: int) -> Product | None:
    result = await session.execute(
        select(Product)
        .where(Product.id == product_id, Product.is_active == True)
        .options(selectinload(Product.photos))
    )
    return result.scalar_one_or_none()