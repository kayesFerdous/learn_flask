from uuid import UUID, uuid4
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learn_flask.extensions import db


class ItemModel(db.Model):
    __tablename__ = "items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)

    store_id: Mapped[int] = mapped_column(db.ForeignKey("stores.id"), nullable=False)
    store: Mapped["StoreModel"] = relationship(back_populates="items") #type: ignore[name-defined]
