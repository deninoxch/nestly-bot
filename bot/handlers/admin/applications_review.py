from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from bot.filters.role_filters import IsAdmin
from bot.keyboards.admin_kb import applications_list_keyboard, application_card_keyboard
from core.crud.applications_crud import get_pending_applications, get_application_by_id
from core.database.models.user import User
from core.enums import Language, ApplicationStatus
from core.i18n.translator import get_text

router = Router()
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "apps:list")
async def show_applications_list(callback: CallbackQuery, lang: Language, session: AsyncSession):
    applications = await get_pending_applications(session)

    text = get_text("pending_applications_title", lang) if applications else get_text("no_pending_applications", lang)

    await callback.message.edit_text(
        text,
        reply_markup=applications_list_keyboard(applications, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("app_view:"))
async def show_application_card(callback: CallbackQuery, lang: Language, session: AsyncSession):
    application_id = int(callback.data.split(":")[1])
    application = await get_application_by_id(session, application_id)

    text = (
        f"🏢 {application.company_name}\n"
        f"📞 {application.contact_info}\n\n"
        f"💬 {application.message}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=application_card_keyboard(application.id, application.applicant.telegram_id, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("app_accept:"))
async def accept_application(callback: CallbackQuery, lang: Language, session: AsyncSession, user: User, bot: Bot):
    await _resolve_application(callback, session, user, bot, ApplicationStatus.ACCEPTED)


@router.callback_query(F.data.startswith("app_reject:"))
async def reject_application(callback: CallbackQuery, lang: Language, session: AsyncSession, user: User, bot: Bot):
    await _resolve_application(callback, session, user, bot, ApplicationStatus.REJECTED)


async def _resolve_application(
    callback: CallbackQuery, session: AsyncSession, admin: User, bot: Bot, new_status: ApplicationStatus
):
    application_id = int(callback.data.split(":")[1])
    application = await get_application_by_id(session, application_id)

    application.status = new_status
    application.reviewed_by = admin.id
    application.reviewed_at = datetime.utcnow()
    await session.commit()

    applicant = application.applicant
    notification_key = "application_accepted" if new_status == ApplicationStatus.ACCEPTED else "application_rejected"
    try:
        await bot.send_message(
            applicant.telegram_id,
            get_text(notification_key, applicant.language),
        )
    except Exception:
        pass

    applications = await get_pending_applications(session)
    await callback.message.edit_text(
        get_text("pending_applications_title", admin.language) if applications else get_text("no_pending_applications", admin.language),
        reply_markup=applications_list_keyboard(applications, admin.language),
    )
    await callback.answer(get_text("application_processed", admin.language))