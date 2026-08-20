from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database.base import Base
from core.enums import ApplicationStatus

class Application(Base):
    __tablename__ = 'applications'

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_info: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[ApplicationStatus] = mapped_column(default=ApplicationStatus.PENDING)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    applicant: Mapped["User"] = relationship(foreign_keys=[user_id])
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by])

    def __repr__(self) -> str:
        return f"<Application id={self.id} status={self.status} company={self.company_name}>"  