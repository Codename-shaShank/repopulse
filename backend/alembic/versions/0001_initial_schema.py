"""Create repository, snapshot, language and sync run tables

Revision ID: 0001
Revises:
Create Date: 2026-11-09
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None



def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "repository",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=512), nullable=False),
        sa.Column("html_url", sa.String(length=1024), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("primary_language", sa.String(length=128), nullable=True),
        sa.Column("stars_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("forks_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("open_issues_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("watchers_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("github_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("full_name", name="ux_repository_full_name"),
    )
    op.execute(
        "CREATE UNIQUE INDEX ux_repository_full_name_lower "
        "ON repository (lower(full_name))"
    )

    op.create_table(
        "repository_snapshot",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "repository_id",
            sa.Uuid(),
            sa.ForeignKey("repository.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stars_count", sa.Integer(), nullable=False),
        sa.Column("forks_count", sa.Integer(), nullable=False),
        sa.Column("open_issues_count", sa.Integer(), nullable=False),
        sa.Column("watchers_count", sa.Integer(), nullable=False),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_repository_snapshot_repo_captured",
        "repository_snapshot",
        ["repository_id", "captured_at"],
    )

    op.create_table(
        "language_stat",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "snapshot_id",
            sa.Uuid(),
            sa.ForeignKey("repository_snapshot.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("language", sa.String(length=128), nullable=False),
        sa.Column("bytes_of_code", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint(
            "snapshot_id", "language", name="ux_language_stat_snapshot_language"
        ),
    )
    op.create_index("ix_language_stat_snapshot", "language_stat", ["snapshot_id"])

    op.create_table(
        "sync_run",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "repository_id",
            sa.Uuid(),
            sa.ForeignKey("repository.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "records_processed", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status in ('in_progress', 'success', 'failed')",
            name="ck_sync_run_status",
        ),
    )
    op.create_index(
        "ix_sync_run_repo_started", "sync_run", ["repository_id", "started_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_sync_run_repo_started", table_name="sync_run")
    op.drop_table("sync_run")

    op.drop_index("ix_language_stat_snapshot", table_name="language_stat")
    op.drop_table("language_stat")

    op.drop_index(
        "ix_repository_snapshot_repo_captured", table_name="repository_snapshot"
    )
    op.drop_table("repository_snapshot")

    op.execute("DROP INDEX IF EXISTS ux_repository_full_name_lower")
    op.drop_table("repository")
