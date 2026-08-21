from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from core.i18n.translator import get_text
from core.enums import Language

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, lang: Language):
    text = get_text("welcome_message", lang)
    await message.answer(text)