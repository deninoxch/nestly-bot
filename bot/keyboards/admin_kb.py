from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database.models.user import User
from core.enums import Language
from core.i18n.translator import get_text


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