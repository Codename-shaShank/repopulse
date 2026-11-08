import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, Integer, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.snapshot import RepositorySnapshot
    from app.models.sync_run import SyncRun


class Repository(TimestampMixin, Base):
    __tablename__ = "repository"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    html_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_language: Mapped[str | None] = mapped_column(String(128), nullable=True)

    stars_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    forks_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    open_issues_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    watchers_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    github_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    snapshots: Mapped[list["RepositorySnapshot"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RepositorySnapshot.captured_at",
    )
    sync_runs: Mapped[list["SyncRun"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SyncRun.started_at.desc()",
    )

    __table_args__ = (
        Index(
            "ux_repository_full_name_lower", text("lower(full_name)"), unique=True
        ),
    )
