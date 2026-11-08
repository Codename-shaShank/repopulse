import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.language_stat import LanguageStat
    from app.models.repository import Repository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RepositorySnapshot(Base):
    """Append-only history: one row per successful sync, never updated in place."""

    __tablename__ = "repository_snapshot"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("repository.id", ondelete="CASCADE"), nullable=False
    )

    stars_count: Mapped[int] = mapped_column(Integer, nullable=False)
    forks_count: Mapped[int] = mapped_column(Integer, nullable=False)
    open_issues_count: Mapped[int] = mapped_column(Integer, nullable=False)
    watchers_count: Mapped[int] = mapped_column(Integer, nullable=False)

    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    repository: Mapped["Repository"] = relationship(back_populates="snapshots")
    languages: Mapped[list["LanguageStat"]] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LanguageStat.bytes_of_code.desc()",
    )

    __table_args__ = (
        Index("ix_repository_snapshot_repo_captured", "repository_id", "captured_at"),
    )
