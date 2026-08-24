from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.role_filters import IsAdmin
from bot.states.product_states import EditProductStates
from bot.keyboards.admin_kb import (
    manage_categories_keyboard,
    manage_products_categories_keyboard,
    manage_products_list_keyboard,
    product_manage_card_keyboard,
)
from core.crud.categories_crud import get_all_categories, get_category_by_id, toggle_category_active, get_leaf_categories
from core.crud.products_crud import get_all_products_by_category, get_product_by_id, toggle_product_active, update_product_price
from core.enums import Language
from core.i18n.translator import get_text
from core.logger import logger

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "manage_categories")
async def show_manage_categories(callback: CallbackQuery, lang: Language, session: AsyncSession):
    categories = await get_all_categories(session)
    await callback.message.edit_text(
        get_text("manage_categories_title", lang),
        reply_markup=manage_categories_keyboard(categories, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_cat:"))
async def toggle_category(callback: CallbackQuery, lang: Language, session: AsyncSession):
    category_id = int(callback.data.split(":")[1])
    category = await get_category_by_id(session, category_id)

    await toggle_category_active(session, category)
    logger.info(f"Category {category_id} active set to {category.is_active} by admin_id via {callback.from_user.id}")

    categories = await get_all_categories(session)
    await callback.message.edit_text(
        get_text("manage_categories_title", lang),
        reply_markup=manage_categories_keyboard(categories, lang),
    )
    await callback.answer()


@router.callback_query(F.data == "manage_products_cats")
async def show_manage_products_categories(callback: CallbackQuery, lang: Language, session: AsyncSession):
    categories = await get_leaf_categories(session)

    if not categories:
        await callback.answer(get_text("no_leaf_categories", lang), show_alert=True)
        return

    await callback.message.edit_text(
        get_text("choose_category_to_manage", lang),
        reply_markup=manage_products_categories_keyboard(categories, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("manage_prod_cat:"))
async def show_manage_products_list(callback: CallbackQuery, lang: Language, session: AsyncSession):
    category_id = int(callback.data.split(":")[1])
    products = await get_all_products_by_category(session, category_id)

    text = get_text("manage_products_title", lang) if products else get_text("no_products", lang)

    await callback.message.edit_text(
        text,
        reply_markup=manage_products_list_keyboard(products, category_id, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("manage_prod:"))
async def show_product_manage_card(callback: CallbackQuery, lang: Language, session: AsyncSession):
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(session, product_id)

    name = product.name_ru if lang == Language.RU else product.name_en
    status = get_text("status_active", lang) if product.is_active else get_text("status_hidden", lang)
    text = f"🛋 <b>{name}</b>\n💰 {product.price} ₽\n📌 {status}"

    await callback.message.edit_text(
        text,
        reply_markup=product_manage_card_keyboard(product.id, product.category_id, product.is_active, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_prod:"))
async def toggle_product(callback: CallbackQuery, lang: Language, session: AsyncSession):
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(session, product_id)

    await toggle_product_active(session, product)
    logger.info(f"Product {product_id} active set to {product.is_active} by admin via {callback.from_user.id}")

    name = product.name_ru if lang == Language.RU else product.name_en
    status = get_text("status_active", lang) if product.is_active else get_text("status_hidden", lang)
    text = f"🛋 <b>{name}</b>\n💰 {product.price} ₽\n📌 {status}"

    await callback.message.edit_text(
        text,
        reply_markup=product_manage_card_keyboard(product.id, product.category_id, product.is_active, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_price:"))
async def start_edit_price(callback: CallbackQuery, lang: Language, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    await state.update_data(edit_product_id=product_id)
    await callback.message.edit_text(get_text("enter_new_price", lang))
    await state.set_state(EditProductStates.waiting_for_new_price)
    await callback.answer()


@router.message(StateFilter(EditProductStates.waiting_for_new_price))
async def process_new_price(message: Message, lang: Language, session: AsyncSession, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError
    except (ValueError, AttributeError, TypeError):
        await message.answer(get_text("invalid_price", lang))
        return

    data = await state.get_data()
    product_id = data["edit_product_id"]
    product = await get_product_by_id(session, product_id)

    await update_product_price(session, product, price)
    logger.info(f"Product {product_id} price updated to {price} by admin via {message.from_user.id}")

    await state.clear()
    name = product.name_ru if lang == Language.RU else product.name_en
    status = get_text("status_active", lang) if product.is_active else get_text("status_hidden", lang)
    text = f"🛋 <b>{name}</b>\n💰 {product.price} ₽\n📌 {status}"

    await message.answer(
        get_text("price_updated", lang),
        reply_markup=product_manage_card_keyboard(product.id, product.category_id, product.is_active, lang),
    )