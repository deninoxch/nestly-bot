from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.application_states import CooperationStates
from core.crud.applications_crud import get_all_admins
from core.database.models.application import Application
from core.database.models.user import User
from core.enums import Language
from core.i18n.translator import get_text

router = Router()


@router.callback_query(F.data == "cooperation:start")
async def start_cooperation(callback: CallbackQuery, lang: Language, state: FSMContext):
    await callback.message.edit_text(get_text("enter_company_name", lang))
    await state.set_state(CooperationStates.waiting_for_company_name)
    await callback.answer()


@router.message(StateFilter(CooperationStates.waiting_for_company_name))
async def process_company_name(message: Message, lang: Language, state: FSMContext):
    await state.update_data(company_name=message.text)
    await message.answer(get_text("enter_contact_info", lang))
    await state.set_state(CooperationStates.waiting_for_contact_info)


@router.message(StateFilter(CooperationStates.waiting_for_contact_info))
async def process_contact_info(message: Message, lang: Language, state: FSMContext):
    await state.update_data(contact_info=message.text)
    await message.answer(get_text("enter_cooperation_message", lang))
    await state.set_state(CooperationStates.waiting_for_message)


@router.message(StateFilter(CooperationStates.waiting_for_message))
async def process_cooperation_message(
    message: Message, lang: Language, session: AsyncSession, state: FSMContext, user: User, bot: Bot
):
    data = await state.get_data()

    new_application = Application(
        user_id=user.id,
        company_name=data["company_name"],
        contact_info=data["contact_info"],
        message=message.text,
    )
    session.add(new_application)
    await session.commit()
    await session.refresh(new_application)

    await state.clear()
    await message.answer(get_text("application_submitted", lang))

    admins = await get_all_admins(session)
    for admin in admins:
        try:
            await bot.send_message(
                admin.telegram_id,
                get_text("new_application_notification", admin.language).format(
                    company=new_application.company_name,
                    contact=new_application.contact_info,
                ),
            )
        except Exception:
            pass