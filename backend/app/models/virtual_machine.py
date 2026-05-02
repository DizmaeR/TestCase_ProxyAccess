from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class VirtualMachine(Base):
    __tablename__ = "virtual_machines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    host: Mapped[str] = mapped_column(String)
    port: Mapped[int] = mapped_column()
    protocol: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=False)
    current_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    current_user = relationship("User", back_populates="virtual_machine")
