from sqlalchemy.orm import Mapped, mapped_column, relationship
from learn_flask.extensions import db

class StoreModel(db.Model):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    items: Mapped[list["ItemModel"]] = relationship(back_populates="store", cascade="all, delete-orphan", lazy="dynamic") #type: ignore[name-defined]
