import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.snapshot import RepositorySnapshot


class LanguageStat(Base):
    """Language composition as of one snapshot, so syncs stay comparable."""

    __tablename__ = "language_stat"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("repository_snapshot.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(128), nullable=False)
    bytes_of_code: Mapped[int] = mapped_column(BigInteger, nullable=False)

    snapshot: Mapped["RepositorySnapshot"] = relationship(back_populates="languages")

    __table_args__ = (
        UniqueConstraint(
            "snapshot_id", "language", name="ux_language_stat_snapshot_language"
        ),
        Index("ix_language_stat_snapshot", "snapshot_id"),
    )
