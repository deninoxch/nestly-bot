from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.role_filters import IsAdmin
from bot.states.product_states import AddCategoryStates
from bot.keyboards.admin_kb import categories_selection_keyboard, cancel_keyboard
from core.crud.categories_crud import get_categories_by_parent, get_category_by_id
from core.database.models.category import Category
from core.enums import Language
from core.i18n.translator import get_text
from bot.handlers.user.catalog import render_main_menu

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("add_category"))
async def cmd_add_category(message: Message, lang: Language, session: AsyncSession, state: FSMContext):
    categories = await get_categories_by_parent(session, parent_id=None)

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
    await state.update_data(name_ru=message.text)
    await message.answer(get_text("enter_category_name_en", lang))
    await state.set_state(AddCategoryStates.waiting_for_name_en)


from core.utils import contains_cyrillic

@router.message(StateFilter(AddCategoryStates.waiting_for_name_en))
async def process_category_name_en(message: Message, lang: Language, session: AsyncSession, state: FSMContext):
    if contains_cyrillic(message.text):
        await message.answer(get_text("must_be_english", lang))
        return

    data = await state.get_data()

    new_category = Category(
        parent_id=data["parent_id"],
        name_ru=data["name_ru"],
        name_en=message.text,
    )
    session.add(new_category)
    await session.commit()

    await state.clear()
    await message.answer(get_text("category_added", lang))
    await render_main_menu(message, lang, session, edit=False)