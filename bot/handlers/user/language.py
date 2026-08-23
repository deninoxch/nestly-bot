from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.user import User
from core.enums import Language
from core.i18n.translator import get_text
from bot.keyboards.user_kb import language_keyboard

router = Router()


@router.message(Command("language"))
async def cmd_language(message: Message, lang: Language, state: FSMContext):
    await state.clear()
    await message.answer(
        get_text("choose_language", lang),
        reply_markup=language_keyboard(lang),
    )


@router.callback_query(F.data == "menu:language")
async def show_language_menu(callback: CallbackQuery, lang: Language, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        get_text("choose_language", lang),
        reply_markup=language_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def process_language_choice(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
):
    new_lang_code = callback.data.split(":")[1]
    new_lang = Language(new_lang_code)

    user.language = new_lang
    await session.commit()

    from bot.handlers.user.catalog import render_main_menu
    await render_main_menu(callback.message, new_lang, session, edit=True)
    await callback.answer(get_text("language_changed", new_lang))