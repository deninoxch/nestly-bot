import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from core.config import settings
from bot.handlers.user import catalog as user_catalog
from bot.middlewares.db_session_middleware import DbSessionMiddleware
from bot.middlewares.i18n_middleware import I18nMiddleware


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(I18nMiddleware())

    dp.include_router(user_catalog.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())