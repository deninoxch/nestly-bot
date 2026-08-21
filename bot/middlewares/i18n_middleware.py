from typing import Callable, Awaitable, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy import select

from core.database.models.user import User 
from core.enums import Language

class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session = data['session']
        tg_user: TgUser | None = data.get("event_from_user")


        if tg_user is None:
            return await handler(event, data)

        result = await session.execute(
            select(User).where(User.telegram_id == tg_user.id)
        )
        db_user = result.scalar_one_or_none()

        if db_user is None:
            db_user = User(
                telegram_id=tg_user.id,
                full_name=tg_user.full_name,
                language=Language.RU,
            )
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)

        data['user'] = db_user
        data['lang'] = db_user.language

        return await handler(event, data)