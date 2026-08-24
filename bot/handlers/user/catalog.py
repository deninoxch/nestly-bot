from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud.categories_crud import get_categories_by_parent, get_category_by_id
from core.crud.products_crud import (
    get_products_by_category,
    get_product_by_id,
    get_distinct_countries,
    get_products_by_category_and_country,
)
from core.enums import Language, Country
from core.i18n.translator import get_text
from bot.keyboards.user_kb import (
    categories_keyboard,
    products_list_keyboard,
    product_card_keyboard,
    country_filter_keyboard,
)

router = Router()


async def safe_edit_text(message: Message, text: str, reply_markup=None):
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


async def safe_edit_media(message: Message, media, reply_markup=None):
    try:
        await message.edit_media(media=media, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


async def safe_edit_or_resend(message: Message, text: str, reply_markup=None):
    if message.photo:
        await message.delete()
        await message.answer(text, reply_markup=reply_markup)
    else:
        await safe_edit_text(message, text, reply_markup=reply_markup)


async def render_main_menu(message_or_callback_message, lang: Language, session: AsyncSession, edit: bool = False):
    categories = await get_categories_by_parent(session, parent_id=None)
    text = get_text("welcome_message", lang)
    markup = categories_keyboard(categories, lang, parent_id=None, is_root=True)

    if edit:
        await safe_edit_or_resend(message_or_callback_message, text, reply_markup=markup)
    else:
        await message_or_callback_message.answer(text, reply_markup=markup)


@router.message(CommandStart())
async def cmd_start(message: Message, lang: Language, session: AsyncSession, state: FSMContext):
    await state.clear()
    await render_main_menu(message, lang, session, edit=False)


@router.callback_query(F.data == "menu:main")
async def show_main_menu(callback: CallbackQuery, lang: Language, session: AsyncSession, state: FSMContext):
    await state.clear()
    await render_main_menu(callback.message, lang, session, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def show_category(callback: CallbackQuery, lang: Language, session: AsyncSession):
    category_id = int(callback.data.split(":")[1])

    current_category = await get_category_by_id(session, category_id)
    subcategories = await get_categories_by_parent(session, parent_id=category_id)
    name = current_category.name_ru if lang == Language.RU else current_category.name_en

    if subcategories:
        await safe_edit_or_resend(
            callback.message,
            name,
            reply_markup=categories_keyboard(
                subcategories, lang, parent_id=current_category.parent_id
            ),
        )
    else:
        countries = await get_distinct_countries(session, category_id)

        if len(countries) > 1:
            await safe_edit_or_resend(
                callback.message,
                f"📦 {name}\n\n{get_text('choose_country', lang)}",
                reply_markup=country_filter_keyboard(
                    countries, category_id, current_category.parent_id, lang
                ),
            )
        elif len(countries) == 1:
            products = await get_products_by_category_and_country(session, category_id, countries[0])
            await safe_edit_or_resend(
                callback.message,
                f"📦 {name}",
                reply_markup=products_list_keyboard(products, current_category.parent_id, lang),
            )
        else:
            await safe_edit_or_resend(
                callback.message,
                f"📦 {name}\n\n{get_text('no_products', lang)}",
                reply_markup=categories_keyboard([], lang, parent_id=current_category.parent_id),
            )

    await callback.answer()


@router.callback_query(F.data.startswith("prodcountry:"))
async def show_products_by_country(callback: CallbackQuery, lang: Language, session: AsyncSession):
    _, category_id_str, country_value = callback.data.split(":")
    category_id = int(category_id_str)
    country = Country(country_value)

    current_category = await get_category_by_id(session, category_id)
    products = await get_products_by_category_and_country(session, category_id, country)
    name = current_category.name_ru if lang == Language.RU else current_category.name_en

    await safe_edit_or_resend(
        callback.message,
        f"📦 {name}",
        reply_markup=products_list_keyboard(products, current_category.parent_id, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def show_product_card(callback: CallbackQuery, lang: Language, session: AsyncSession):
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(session, product_id)

    caption = _build_product_caption(product, lang)
    keyboard = product_card_keyboard(
        product_id=product.id,
        category_id=product.category_id,
        photo_index=0,
        total_photos=len(product.photos),
        lang=lang,
    )

    if product.photos:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product.photos[0].file_id,
            caption=caption,
            reply_markup=keyboard,
        )
    else:
        await safe_edit_text(callback.message, caption, reply_markup=keyboard)

    await callback.answer()


@router.callback_query(F.data.startswith("photo:"))
async def switch_photo(callback: CallbackQuery, lang: Language, session: AsyncSession):
    _, product_id_str, index_str = callback.data.split(":")
    product_id = int(product_id_str)
    photo_index = int(index_str)

    product = await get_product_by_id(session, product_id)
    caption = _build_product_caption(product, lang)
    keyboard = product_card_keyboard(
        product_id=product.id,
        category_id=product.category_id,
        photo_index=photo_index,
        total_photos=len(product.photos),
        lang=lang,
    )

    await safe_edit_media(
        callback.message,
        InputMediaPhoto(media=product.photos[photo_index].file_id, caption=caption),
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    await callback.answer()


def _build_product_caption(product, lang: Language) -> str:
    name = product.name_ru if lang == Language.RU else product.name_en
    description = product.description_ru if lang == Language.RU else product.description_en
    country_label = get_text(f"country_{product.country.value}", lang)

    lines = [f"🛋 <b>{name}</b>", ""]

    if description:
        lines.append(description)
        lines.append("")

    lines.append(f"🌍 {get_text('made_in', lang)}: {country_label}")
    lines.append(f"💰 {get_text('price_label', lang)}: {product.price} ₽")

    return "\n".join(lines)

from bot.keyboards.user_kb import other_menu_keyboard


@router.callback_query(F.data == "menu:other")
async def show_other_menu(callback: CallbackQuery, lang: Language):
    await safe_edit_or_resend(
        callback.message,
        get_text("other_menu_title", lang),
        reply_markup=other_menu_keyboard(lang),
    )
    await callback.answer()