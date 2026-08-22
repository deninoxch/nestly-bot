from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database.models.user import User
from core.enums import Language
from core.i18n.translator import get_text

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.category import Category


def admin_panel_keyboard(lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_manage_admins", lang), callback_data="admins:list")
    builder.adjust(1)
    return builder.as_markup()


def admins_list_keyboard(admins: list[User], lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for admin in admins:
        label = admin.full_name or str(admin.telegram_id)
        builder.button(text=f"❌ {label}", callback_data=f"admin_remove:{admin.id}")

    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_add_admin", lang), callback_data="admin_add"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_back", lang), callback_data="admin_panel:main"
        )
    )

    return builder.as_markup()


async def categories_selection_keyboard(
    session: AsyncSession, lang: Language, current_parent_id
) -> InlineKeyboardMarkup:
    result = await session.execute(select(Category).order_by(Category.id))
    all_categories = list(result.scalars().all())

    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("no_parent_root", lang), callback_data="selectparent:none")

    for category in all_categories:
        name = category.name_ru if lang == Language.RU else category.name_en
        builder.button(text=name, callback_data=f"selectparent:{category.id}")

    builder.adjust(1)
    return builder.as_markup()


def cancel_keyboard(lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_cancel", lang), callback_data="admin_cancel")
    return builder.as_markup()