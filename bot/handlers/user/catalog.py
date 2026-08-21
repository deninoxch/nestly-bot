from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud.categories_crud import get_categories_by_parent, get_category_by_id
from core.crud.products_crud import get_products_by_category, get_product_by_id
from core.enums import Language
from core.i18n.translator import get_text
from bot.keyboards.user_kb import (
    categories_keyboard,
    products_list_keyboard,
    product_card_keyboard,
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


@router.message(CommandStart())
async def cmd_start(message: Message, lang: Language, session: AsyncSession):
    categories = await get_categories_by_parent(session, parent_id=None)

    if not categories:
        await message.answer(get_text("welcome_message", lang))
        return

    await message.answer(
        get_text("welcome_message", lang),
        reply_markup=categories_keyboard(categories, lang, parent_id=None, is_root=True),
    )


@router.callback_query(F.data == "menu:main")
async def show_main_menu(callback: CallbackQuery, lang: Language, session: AsyncSession):
    categories = await get_categories_by_parent(session, parent_id=None)

    await safe_edit_text(
        callback.message,
        get_text("welcome_message", lang),
        reply_markup=categories_keyboard(categories, lang, parent_id=None, is_root=True),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def show_category(callback: CallbackQuery, lang: Language, session: AsyncSession):
    category_id = int(callback.data.split(":")[1])

    current_category = await get_category_by_id(session, category_id)
    subcategories = await get_categories_by_parent(session, parent_id=category_id)

    if subcategories:
        name = current_category.name_ru if lang == Language.RU else current_category.name_en
        await safe_edit_text(
            callback.message,
            name,
            reply_markup=categories_keyboard(
                subcategories, lang, parent_id=current_category.parent_id
            ),
        )
    else:
        products = await get_products_by_category(session, category_id)
        name = current_category.name_ru if lang == Language.RU else current_category.name_en

        if not products:
            await safe_edit_text(
                callback.message,
                f"📦 {name}\n\n{get_text('no_products', lang)}",
                reply_markup=categories_keyboard(
                    [], lang, parent_id=current_category.parent_id
                ),
            )
        else:
            await safe_edit_text(
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
    description = description or ""

    return f"<b>{name}</b>\n\n{description}\n\n💰 {product.price} ₽"