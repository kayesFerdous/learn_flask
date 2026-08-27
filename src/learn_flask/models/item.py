from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship

from learn_flask.extensions import Base, db
from learn_flask.models.item_tags import items_tags


class ItemModel(Base):
    __tablename__ = "items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column(nullable=False)

    store_id: Mapped[int] = mapped_column(db.ForeignKey("stores.id"), nullable=False)

    store: Mapped["StoreModel"] = relationship(back_populates="items")
    tags: Mapped[list["TagModel"]] = relationship(
        back_populates="items", secondary=items_tags
    )
