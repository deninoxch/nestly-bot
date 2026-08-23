from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.role_filters import IsSuperAdmin
from bot.keyboards.admin_kb import admin_panel_keyboard, admins_list_keyboard, users_selection_keyboard
from core.crud.users_crud import get_admins, get_user_by_telegram_id, set_user_role, get_regular_users
from core.enums import Language, UserRole
from core.i18n.translator import get_text

from core.logger import logger

router = Router()
router.message.filter(IsSuperAdmin())
router.callback_query.filter(IsSuperAdmin())


@router.message(Command("admin_panel"))
async def cmd_admin_panel(message: Message, lang: Language, state: FSMContext):
    await state.clear()
    await message.answer(
        get_text("admin_panel_title", lang),
        reply_markup=admin_panel_keyboard(lang),
    )


@router.callback_query(F.data == "admin_panel:main")
async def show_admin_panel(callback: CallbackQuery, lang: Language, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        get_text("admin_panel_title", lang),
        reply_markup=admin_panel_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "admins:list")
async def show_admins_list(callback: CallbackQuery, lang: Language, session: AsyncSession):
    admins = await get_admins(session)

    if not admins:
        text = get_text("no_admins_yet", lang)
    else:
        text = get_text("current_admins_title", lang)

    await callback.message.edit_text(
        text,
        reply_markup=admins_list_keyboard(admins, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_remove:"))
async def remove_admin(callback: CallbackQuery, lang: Language, session: AsyncSession):
    from core.database.models.user import User
    from sqlalchemy import select

    user_id = int(callback.data.split(":")[1])
    result = await session.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if target_user is None or target_user.role != UserRole.ADMIN:
        await callback.answer(get_text("action_not_allowed", lang), show_alert=True)
        return

    await set_user_role(session, target_user, UserRole.USER)
    logger.info(f"Admin role removed: user_id={target_user.id}, by superadmin_id={callback.from_user.id}")

    admins = await get_admins(session)
    await callback.message.edit_text(
        get_text("current_admins_title", lang) if admins else get_text("no_admins_yet", lang),
        reply_markup=admins_list_keyboard(admins, lang),
    )
    await callback.answer(get_text("admin_removed", lang))
    
@router.callback_query(F.data == "admin_add")
async def start_add_admin(callback: CallbackQuery, lang: Language, session: AsyncSession):
    users = await get_regular_users(session)

    if not users:
        await callback.answer(get_text("no_users_to_promote", lang), show_alert=True)
        return

    await callback.message.edit_text(
        get_text("choose_user_to_promote", lang),
        reply_markup=users_selection_keyboard(users, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("makeadmin:"))
async def process_make_admin(callback: CallbackQuery, lang: Language, session: AsyncSession):
    telegram_id = int(callback.data.split(":")[1])
    target_user = await get_user_by_telegram_id(session, telegram_id)

    if target_user:
        await set_user_role(session, target_user, UserRole.ADMIN)
        logger.info(f"User promoted to admin: telegram_id={telegram_id}, by superadmin_id={callback.from_user.id}")

    admins = await get_admins(session)
    await callback.message.edit_text(get_text("admin_added", lang))
    await callback.message.answer(
        get_text("current_admins_title", lang) if admins else get_text("no_admins_yet", lang),
        reply_markup=admins_list_keyboard(admins, lang),
    )
    await callback.answer()