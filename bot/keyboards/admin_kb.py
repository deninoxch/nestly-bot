from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database.models.user import User
from core.enums import Language
from core.i18n.translator import get_text

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.enums import Country

from core.database.models.category import Category
from core.enums import ApplicationStatus
from core.database.models.product import Product

def admin_panel_keyboard(lang: Language, is_superadmin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_view_applications", lang), callback_data="apps:list")
    builder.button(text=get_text("btn_add_category_panel", lang), callback_data="panel_add_category")
    builder.button(text=get_text("btn_add_product_panel", lang), callback_data="panel_add_product")
    builder.button(text=get_text("btn_manage_categories", lang), callback_data="manage_categories")
    builder.button(text=get_text("btn_manage_products", lang), callback_data="manage_products_cats")

    if is_superadmin:
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

def leaf_categories_keyboard(categories: list[Category], lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for category in categories:
        name = category.name_ru if lang == Language.RU else category.name_en
        builder.button(text=name, callback_data=f"selectcat:{category.id}")

    builder.adjust(1)
    return builder.as_markup()



def country_selection_keyboard(lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Россия" if lang == Language.RU else "🇷🇺 Russia", callback_data="selectcountry:RUSSIA")
    builder.button(text="🇺🇸 США" if lang == Language.RU else "🇺🇸 USA", callback_data="selectcountry:USA")
    builder.adjust(2)
    return builder.as_markup()


def skip_keyboard(lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_skip", lang), callback_data="skip_step")
    return builder.as_markup()


def finish_photos_keyboard(lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_finish_photos", lang), callback_data="finish_photos")
    return builder.as_markup()

def users_selection_keyboard(users: list[User], lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for u in users:
        label = u.full_name or str(u.telegram_id)
        builder.button(text=label, callback_data=f"makeadmin:{u.telegram_id}")

    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admins:list")
    )

    return builder.as_markup()


from core.database.models.application import Application


def applications_list_keyboard(applications: list[Application], lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for app in applications:
        builder.button(text=f"📋 {app.company_name}", callback_data=f"app_view:{app.id}")

    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=get_text("btn_history", lang), callback_data="apps:history")
    )
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin_panel:main")
    )
    return builder.as_markup()


def application_card_keyboard(application_id: int, applicant_telegram_id: int, lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_accept", lang), callback_data=f"app_accept:{application_id}")
    builder.button(text=get_text("btn_reject", lang), callback_data=f"app_reject:{application_id}")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_message_applicant", lang),
            url=f"tg://user?id={applicant_telegram_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="apps:list")
    )
    return builder.as_markup()

def applications_history_keyboard(applications: list[Application], lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for app in applications:
        status_icon = "✅" if app.status == ApplicationStatus.ACCEPTED else "❌"
        builder.button(text=f"{status_icon} {app.company_name}", callback_data=f"app_view_history:{app.id}")

    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="apps:list")
    )
    return builder.as_markup()

def history_card_keyboard(application_id: int, lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_delete", lang), callback_data=f"app_delete_confirm:{application_id}")
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="apps:history")
    )
    return builder.as_markup()


def delete_confirmation_keyboard(application_id: int, lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_confirm_delete", lang), callback_data=f"app_delete:{application_id}")
    builder.button(text=get_text("btn_cancel", lang), callback_data=f"app_view_history:{application_id}")
    builder.adjust(2)
    return builder.as_markup()

def manage_categories_keyboard(categories: list[Category], lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for c in categories:
        name = c.name_ru if lang == Language.RU else c.name_en
        icon = "🟢" if c.is_active else "🔴"
        builder.button(text=f"{icon} {name}", callback_data=f"toggle_cat:{c.id}")

    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin_panel:main")
    )
    return builder.as_markup()


def manage_products_categories_keyboard(categories: list[Category], lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for c in categories:
        name = c.name_ru if lang == Language.RU else c.name_en
        builder.button(text=name, callback_data=f"manage_prod_cat:{c.id}")

    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin_panel:main")
    )
    return builder.as_markup()


def manage_products_list_keyboard(products: list[Product], category_id: int, lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for p in products:
        name = p.name_ru if lang == Language.RU else p.name_en
        icon = "🟢" if p.is_active else "🔴"
        builder.button(text=f"{icon} {name}", callback_data=f"manage_prod:{p.id}")

    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="manage_products_cats")
    )
    return builder.as_markup()


def product_manage_card_keyboard(product_id: int, category_id: int, is_active: bool, lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    toggle_text = get_text("btn_hide_product", lang) if is_active else get_text("btn_show_product", lang)
    builder.button(text=toggle_text, callback_data=f"toggle_prod:{product_id}")
    builder.button(text=get_text("btn_edit_price", lang), callback_data=f"edit_price:{product_id}")
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_back", lang), callback_data=f"manage_prod_cat:{category_id}"
        )
    )
    return builder.as_markup()