from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

class ProductPhoto(Base):
    __tablename__ = 'product_photos'

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped['Product'] = relationship(back_populates='photos')

    def __repr__(self):
        return f"<ProductPhoto id={self.id} product_id={self.product_id} position={self.position}>"
    