from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud.categories_crud import get_categories_by_parent, get_category_by_id
from core.enums import Language
from core.i18n.translator import get_text
from bot.keyboards.user_kb import categories_keyboard

router = Router()


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

    await callback.message.edit_text(
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
        await callback.message.edit_text(
            name,
            reply_markup=categories_keyboard(
                subcategories, lang, parent_id=current_category.parent_id
            ),
        )
    else:
        name = current_category.name_ru if lang == Language.RU else current_category.name_en
        await callback.message.edit_text(f"📦 {name}\n\n(товары появятся на следующем шаге)")

    await callback.answer()