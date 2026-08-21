from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.base import Base 

class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None ] = mapped_column(
        ForeignKey('categories.id'), nullable=True
    )

    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    products: Mapped[list["Product"]] = relationship(back_populates="category")  

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    parent: Mapped['Category | None'] = relationship(
        remote_side=[id],
        back_populates='children'
    )

    children: Mapped[list["Category"]] = relationship(
        back_populates='parent',
    )

    def __repr__(self) -> str:
        return f'<Category id={self.id} name_ru{self.name_ru} parent_id={self.parent_id}>'