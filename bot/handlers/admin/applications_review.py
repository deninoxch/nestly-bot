from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from bot.filters.role_filters import IsAdmin
from bot.keyboards.admin_kb import (
    applications_list_keyboard,
    application_card_keyboard,
    applications_history_keyboard,
    history_card_keyboard,
    delete_confirmation_keyboard,
)
from core.crud.applications_crud import get_pending_applications, get_application_by_id, get_resolved_applications
from core.database.models.application import Application
from core.database.models.user import User
from core.enums import Language, ApplicationStatus
from core.i18n.translator import get_text
from core.logger import logger

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

    if application is None:
        await callback.answer(get_text("item_not_found", lang), show_alert=True)
        applications = await get_pending_applications(session)
        await callback.message.edit_text(
            get_text("pending_applications_title", lang) if applications else get_text("no_pending_applications", lang),
            reply_markup=applications_list_keyboard(applications, lang),
        )
        return

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

    # Атомарное обновление: меняем статус только если заявка ещё PENDING —
    # защита от гонки, если два админа одновременно нажмут разные кнопки
    result = await session.execute(
        update(Application)
        .where(Application.id == application_id, Application.status == ApplicationStatus.PENDING)
        .values(status=new_status, reviewed_by=admin.id, reviewed_at=datetime.now(timezone.utc))
    )
    await session.commit()

    if result.rowcount == 0:
        await callback.answer(get_text("application_already_resolved", admin.language), show_alert=True)
        applications = await get_pending_applications(session)
        await callback.message.edit_text(
            get_text("pending_applications_title", admin.language) if applications else get_text("no_pending_applications", admin.language),
            reply_markup=applications_list_keyboard(applications, admin.language),
        )
        return

    logger.info(f"Application {application_id} resolved as {new_status.value} by admin_id={admin.id}")

    application = await get_application_by_id(session, application_id)
    applicant = application.applicant
    notification_key = "application_accepted" if new_status == ApplicationStatus.ACCEPTED else "application_rejected"
    try:
        await bot.send_message(
            applicant.telegram_id,
            get_text(notification_key, applicant.language),
        )
    except Exception as e:
        logger.error(f"Failed to notify applicant {applicant.telegram_id}: {e}")

    applications = await get_pending_applications(session)
    await callback.message.edit_text(
        get_text("pending_applications_title", admin.language) if applications else get_text("no_pending_applications", admin.language),
        reply_markup=applications_list_keyboard(applications, admin.language),
    )
    await callback.answer(get_text("application_processed", admin.language))


@router.callback_query(F.data == "apps:history")
async def show_applications_history(callback: CallbackQuery, lang: Language, session: AsyncSession):
    applications = await get_resolved_applications(session)

    text = get_text("applications_history_title", lang) if applications else get_text("no_resolved_applications", lang)

    await callback.message.edit_text(
        text,
        reply_markup=applications_history_keyboard(applications, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("app_view_history:"))
async def show_history_application_card(callback: CallbackQuery, lang: Language, session: AsyncSession):
    application_id = int(callback.data.split(":")[1])
    application = await get_application_by_id(session, application_id)

    if application is None:
        await callback.answer(get_text("item_not_found", lang), show_alert=True)
        applications = await get_resolved_applications(session)
        await callback.message.edit_text(
            get_text("applications_history_title", lang) if applications else get_text("no_resolved_applications", lang),
            reply_markup=applications_history_keyboard(applications, lang),
        )
        return

    status_text = get_text("status_accepted", lang) if application.status == ApplicationStatus.ACCEPTED else get_text("status_rejected", lang)

    text = (
        f"🏢 {application.company_name}\n"
        f"📞 {application.contact_info}\n\n"
        f"💬 {application.message}\n\n"
        f"📌 {get_text('status_label', lang)}: {status_text}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=history_card_keyboard(application.id, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("app_delete_confirm:"))
async def confirm_delete_application(callback: CallbackQuery, lang: Language):
    application_id = int(callback.data.split(":")[1])

    await callback.message.edit_text(
        get_text("confirm_delete_application", lang),
        reply_markup=delete_confirmation_keyboard(application_id, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("app_delete:"))
async def delete_application(callback: CallbackQuery, lang: Language, session: AsyncSession):
    from sqlalchemy import delete

    application_id = int(callback.data.split(":")[1])
    result = await session.execute(delete(Application).where(Application.id == application_id))
    await session.commit()

    if result.rowcount == 0:
        await callback.answer(get_text("item_not_found", lang), show_alert=True)
    else:
        logger.info(f"Application {application_id} deleted by admin_id via callback {callback.from_user.id}")
        await callback.answer(get_text("application_deleted", lang))

    applications = await get_resolved_applications(session)
    text = get_text("applications_history_title", lang) if applications else get_text("no_resolved_applications", lang)

    await callback.message.edit_text(
        text,
        reply_markup=applications_history_keyboard(applications, lang),
    )