from uuid import UUID, uuid4
from sqlalchemy.orm import Mapped, mapped_column

from learn_flask.extensions import db

class ItemModel(db.Model):
    __tablename__ = "items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)


