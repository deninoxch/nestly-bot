from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.role_filters import IsAdmin
from bot.states.product_states import AddCategoryStates, AddProductStates
from bot.keyboards.admin_kb import (
    categories_selection_keyboard,
    leaf_categories_keyboard,
    country_selection_keyboard,
    skip_keyboard,
    finish_photos_keyboard,
)
from bot.handlers.user.catalog import render_main_menu
from core.crud.categories_crud import get_categories_by_parent, get_category_by_id, get_leaf_categories
from core.database.models.category import Category
from core.database.models.product import Product
from core.database.models.photo import ProductPhoto
from core.database.models.user import User
from core.enums import Language, Country
from core.i18n.translator import get_text
from core.utils import contains_cyrillic

from core.logger import logger

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())



@router.message(Command("add_category"))
async def cmd_add_category(message: Message, lang: Language, session: AsyncSession, state: FSMContext):
    await state.clear()
    await message.answer(
        get_text("choose_parent_category", lang),
        reply_markup=await categories_selection_keyboard(session, lang, current_parent_id=None),
    )
    await state.set_state(AddCategoryStates.waiting_for_parent)


@router.callback_query(
    StateFilter(AddCategoryStates.waiting_for_parent), F.data.startswith("selectparent:")
)
async def process_parent_selection(callback: CallbackQuery, lang: Language, state: FSMContext):
    value = callback.data.split(":")[1]
    parent_id = None if value == "none" else int(value)

    await state.update_data(parent_id=parent_id)
    await callback.message.edit_text(get_text("enter_category_name_ru", lang))
    await state.set_state(AddCategoryStates.waiting_for_name_ru)
    await callback.answer()


@router.message(StateFilter(AddCategoryStates.waiting_for_name_ru))
async def process_category_name_ru(message: Message, lang: Language, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer(get_text("invalid_name", lang))
        return

    await state.update_data(name_ru=message.text.strip())
    await message.answer(get_text("enter_category_name_en", lang))
    await state.set_state(AddCategoryStates.waiting_for_name_en)


@router.message(StateFilter(AddCategoryStates.waiting_for_name_en))
async def process_category_name_en(message: Message, lang: Language, session: AsyncSession, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer(get_text("invalid_name", lang))
        return

    if contains_cyrillic(message.text):
        await message.answer(get_text("must_be_english", lang))
        return

    data = await state.get_data()

    new_category = Category(
        parent_id=data["parent_id"],
        name_ru=data["name_ru"],
        name_en=message.text.strip(),
    )
    session.add(new_category)
    await session.commit()

    session.add(new_category)
    await session.commit()
    logger.info(f"Category created: id={new_category.id}, name_ru={new_category.name_ru}")

    await state.clear()
    await message.answer(get_text("category_added", lang))
    await render_main_menu(message, lang, session, edit=False)

    await state.clear()
    await message.answer(get_text("category_added", lang))
    await render_main_menu(message, lang, session, edit=False)



@router.message(Command("add_product"))
async def cmd_add_product(message: Message, lang: Language, session: AsyncSession, state: FSMContext):
    await state.clear()
    categories = await get_leaf_categories(session)

    if not categories:
        await message.answer(get_text("no_leaf_categories", lang))
        return

    await message.answer(
        get_text("choose_product_category", lang),
        reply_markup=leaf_categories_keyboard(categories, lang),
    )
    await state.set_state(AddProductStates.waiting_for_category)


@router.callback_query(
    StateFilter(AddProductStates.waiting_for_category), F.data.startswith("selectcat:")
)
async def process_product_category(callback: CallbackQuery, lang: Language, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=category_id)

    await callback.message.edit_text(get_text("enter_product_name_ru", lang))
    await state.set_state(AddProductStates.waiting_for_name_ru)
    await callback.answer()


@router.message(StateFilter(AddProductStates.waiting_for_name_ru))
async def process_product_name_ru(message: Message, lang: Language, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer(get_text("invalid_name", lang))
        return

    await state.update_data(name_ru=message.text.strip())
    await message.answer(
        get_text("enter_product_name_en", lang),
    )
    await state.set_state(AddProductStates.waiting_for_name_en)


@router.message(StateFilter(AddProductStates.waiting_for_name_en))
async def process_product_name_en(message: Message, lang: Language, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer(get_text("invalid_name", lang))
        return

    if contains_cyrillic(message.text):
        await message.answer(get_text("must_be_english", lang))
        return

    await state.update_data(name_en=message.text.strip())
    await message.answer(
        get_text("enter_product_description_ru", lang),
        reply_markup=skip_keyboard(lang),
    )
    await state.set_state(AddProductStates.waiting_for_description_ru)


@router.message(StateFilter(AddProductStates.waiting_for_description_ru))
async def process_product_description_ru(message: Message, lang: Language, state: FSMContext):
    await state.update_data(description_ru=message.text)
    await message.answer(
        get_text("enter_product_description_en", lang),
        reply_markup=skip_keyboard(lang),
    )
    await state.set_state(AddProductStates.waiting_for_description_en)


@router.callback_query(
    StateFilter(AddProductStates.waiting_for_description_ru), F.data == "skip_step"
)
async def skip_description_ru(callback: CallbackQuery, lang: Language, state: FSMContext):
    await state.update_data(description_ru=None)
    await callback.message.edit_text(
        get_text("enter_product_description_en", lang),
        reply_markup=skip_keyboard(lang),
    )
    await state.set_state(AddProductStates.waiting_for_description_en)
    await callback.answer()


@router.message(StateFilter(AddProductStates.waiting_for_description_en))
async def process_product_description_en(message: Message, lang: Language, state: FSMContext):
    if contains_cyrillic(message.text):
        await message.answer(get_text("must_be_english", lang))
        return

    await state.update_data(description_en=message.text)
    await message.answer(
        get_text("choose_product_country", lang),
        reply_markup=country_selection_keyboard(lang),
    )
    await state.set_state(AddProductStates.waiting_for_country)


@router.callback_query(
    StateFilter(AddProductStates.waiting_for_description_en), F.data == "skip_step"
)
async def skip_description_en(callback: CallbackQuery, lang: Language, state: FSMContext):
    await state.update_data(description_en=None)
    await callback.message.edit_text(
        get_text("choose_product_country", lang),
        reply_markup=country_selection_keyboard(lang),
    )
    await state.set_state(AddProductStates.waiting_for_country)
    await callback.answer()


@router.callback_query(
    StateFilter(AddProductStates.waiting_for_country), F.data.startswith("selectcountry:")
)
async def process_product_country(callback: CallbackQuery, lang: Language, state: FSMContext):
    country_value = callback.data.split(":")[1]
    await state.update_data(country=Country[country_value])

    await callback.message.edit_text(get_text("enter_product_price", lang))
    await state.set_state(AddProductStates.waiting_for_price)
    await callback.answer()


@router.message(StateFilter(AddProductStates.waiting_for_price))
async def process_product_price(message: Message, lang: Language, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError
    except (ValueError, AttributeError, TypeError):
        await message.answer(get_text("invalid_price", lang))
        return

    await state.update_data(price=price, photos=[])
    await message.answer(get_text("send_product_photos", lang))
    await state.set_state(AddProductStates.waiting_for_photos)


@router.message(StateFilter(AddProductStates.waiting_for_photos), F.photo)
async def process_product_photo(message: Message, lang: Language, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])

    if len(photos) >= 10:
        await message.answer(get_text("max_photos_reached", lang))
        return

    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(photos=photos)

    await message.answer(
        get_text("photo_added", lang).format(count=len(photos)),
        reply_markup=finish_photos_keyboard(lang),
    )


@router.callback_query(
    StateFilter(AddProductStates.waiting_for_photos), F.data == "finish_photos"
)
async def finish_adding_product(
    callback: CallbackQuery, lang: Language, session: AsyncSession, state: FSMContext, user: User
):
    data = await state.get_data()
    photos = data.get("photos", [])

    if not photos:
        await callback.answer(get_text("at_least_one_photo", lang), show_alert=True)
        return

    new_product = Product(
        category_id=data["category_id"],
        created_by=user.id,
        name_ru=data["name_ru"],
        name_en=data["name_en"],
        description_ru=data.get("description_ru"),
        description_en=data.get("description_en"),
        country=data["country"],
        price=data["price"],
    )
    session.add(new_product)
    await session.flush()

    for index, file_id in enumerate(photos):
        session.add(ProductPhoto(product_id=new_product.id, file_id=file_id, position=index))

    await session.commit()
    await session.commit()
    logger.info(f"Product created: id={new_product.id}, name_ru={new_product.name_ru}, by user_id={user.id}")
    await state.clear()

    await callback.message.answer(get_text("product_added", lang))
    await render_main_menu(callback.message, lang, session, edit=False)
    await callback.answer()
    
    await state.clear()

    await callback.message.answer(get_text("product_added", lang))
    await render_main_menu(callback.message, lang, session, edit=False)
    await callback.answer()