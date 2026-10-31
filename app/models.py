from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Note(Base):
    __tablename__ = "notes"

    __table_args__ = (
        UniqueConstraint(
            "title",
            name="uq_notes_title",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
