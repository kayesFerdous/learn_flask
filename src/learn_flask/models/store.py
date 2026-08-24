from sqlalchemy.orm import DynamicMapped, Mapped, mapped_column, relationship
from learn_flask.extensions import Base

class StoreModel(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)

    items: DynamicMapped["ItemModel"] = relationship(back_populates="store", cascade="all, delete-orphan", lazy="dynamic") #type: ignore[name-defined]
