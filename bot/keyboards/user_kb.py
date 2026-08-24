from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database.models.category import Category
from core.enums import Language
from core.i18n.translator import get_text
from core.database.models.product import Product

def language_keyboard(lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="lang:ru")
    builder.button(text="🇬🇧 English", callback_data="lang:en")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="menu:main")
    )
    return builder.as_markup()


def categories_keyboard(
    categories: list[Category],
    lang: Language,
    parent_id: int | None,
    is_root: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for category in categories:
        name = category.name_ru if lang == Language.RU else category.name_en
        builder.button(text=name, callback_data=f"cat:{category.id}")

    builder.adjust(1)

    if is_root:
        builder.row(
            InlineKeyboardButton(text=get_text("menu_other_section", lang), callback_data="menu:other")
        )
    else:
        if parent_id is not None:
            back_callback = f"cat:{parent_id}"
        else:
            back_callback = "menu:main"

        builder.row(
            InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=back_callback)
        )

    return builder.as_markup()

from core.config import settings

def product_card_keyboard(
    product_id: int,
    category_id: int,
    photo_index: int,
    total_photos: int,
    lang: Language,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if total_photos > 1:
        prev_index = (photo_index - 1) % total_photos
        next_index = (photo_index + 1) % total_photos
        builder.row(
            InlineKeyboardButton(text="◀️", callback_data=f"photo:{product_id}:{prev_index}"),
            InlineKeyboardButton(text=f"{photo_index + 1}/{total_photos}", callback_data="noop"),
            InlineKeyboardButton(text="▶️", callback_data=f"photo:{product_id}:{next_index}"),
        )

    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_order", lang),
            url=f"https://t.me/{settings.COMPANY_CONTACT_USERNAME}",
        )
    )
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=f"cat:{category_id}")
    )

    return builder.as_markup()

def products_list_keyboard(
    products: list["Product"],
    parent_id: int | None,
    lang: Language,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for product in products:
        name = product.name_ru if lang == Language.RU else product.name_en
        builder.button(text=f"{name} — {product.price} ₽", callback_data=f"product:{product.id}")

    builder.adjust(1)

    if parent_id is not None:
        back_callback = f"cat:{parent_id}"
    else:
        back_callback = "menu:main"

    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=back_callback)
    )

    return builder.as_markup()

from core.enums import Country


def country_filter_keyboard(
    countries: list[Country],
    category_id: int,
    parent_id: int | None,
    lang: Language,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    flags = {Country.RUSSIA: "🇷🇺", Country.USA: "🇺🇸"}
    names = {
        Country.RUSSIA: {"ru": "Россия", "en": "Russia"},
        Country.USA: {"ru": "США", "en": "USA"},
    }

    for country in countries:
        label = f"{flags[country]} {names[country][lang.value]}"
        builder.button(text=label, callback_data=f"prodcountry:{category_id}:{country.value}")

    builder.adjust(2)

    back_callback = f"cat:{parent_id}" if parent_id is not None else "menu:main"
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=back_callback)
    )

    return builder.as_markup()

def other_menu_keyboard(lang: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_cooperation", lang), callback_data="cooperation:start")
    builder.button(text=get_text("btn_language", lang), callback_data="menu:language")
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="menu:main")
    )
    return builder.as_markup()