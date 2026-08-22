from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from core.database.models.user import User
from core.enums import UserRole

class IsSuperAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject, user: User) -> bool:
        return user.role == UserRole.SUPERADMIN


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject, user: User) -> bool:
        return user.role in (UserRole.ADMIN, UserRole.SUPERADMIN)