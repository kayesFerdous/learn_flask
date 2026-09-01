from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from learn_flask.extensions import Base


class TokenBlocklistModel(Base):
    __tablename__ = "token_blocklist"

    # The "jti" is the unique id JWT gives every token it issues.
    jti: Mapped[str] = mapped_column(primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
