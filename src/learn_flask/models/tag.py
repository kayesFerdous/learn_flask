from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship

from learn_flask.extensions import Base, db
from learn_flask.models.item_tags import items_tags


class TagModel(Base):
    __tablename__ = "tags"
    __table_args__ = (db.UniqueConstraint("store_id", "name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)

    store_id: Mapped[int] = mapped_column(db.ForeignKey("stores.id"), nullable=False)

    store: Mapped["StoreModel"] = relationship(back_populates="tags")
    items: Mapped[list["ItemModel"]] = relationship(
        back_populates="tags", secondary=items_tags
    )
