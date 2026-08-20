from datetime import datetime 

from sqlalchemy import BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database.base import Base
from core.enums import UserRole, Language

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)

    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[Language] = mapped_column(default=Language.RU)
    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at = Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f'<User id={self.id} telegram_id={self.telegram_id} role={self.role}>'