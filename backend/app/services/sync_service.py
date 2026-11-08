import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import GitHubError, NotFoundError
from app.models import LanguageStat, Repository, RepositorySnapshot, SyncRun, SyncStatus
from app.services.github import GitHubClient, GitHubRepository

logger = logging.getLogger(__name__)

MAX_ERROR_LENGTH = 500


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _sanitize(message: str) -> str:
    """Keep the user-facing reason, drop anything that could carry a credential."""
    cleaned = " ".join(str(message).split())
    return cleaned[:MAX_ERROR_LENGTH]


def get_repository(db: Session, repository_id: uuid.UUID) -> Repository:
    repository = db.get(Repository, repository_id)
    if repository is None:
        raise NotFoundError("Tracked repository not found")
    return repository


def latest_snapshot(db: Session, repository_id: uuid.UUID) -> RepositorySnapshot | None:
    return db.scalars(
        select(RepositorySnapshot)
        .where(RepositorySnapshot.repository_id == repository_id)
        .order_by(RepositorySnapshot.captured_at.desc())
        .limit(1)
    ).first()


def latest_languages(db: Session, repository_id: uuid.UUID) -> list[LanguageStat]:
    snapshot = latest_snapshot(db, repository_id)
    if snapshot is None:
        return []
    return list(
        db.scalars(
            select(LanguageStat)
            .where(LanguageStat.snapshot_id == snapshot.id)
            .order_by(LanguageStat.bytes_of_code.desc())
        ).all()
    )


def snapshot_count(db: Session, repository_id: uuid.UUID) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(RepositorySnapshot)
            .where(RepositorySnapshot.repository_id == repository_id)
        )
        or 0
    )


def _apply_metadata(repository: Repository, data: GitHubRepository) -> None:
    repository.owner = data.owner
    repository.name = data.name
    repository.full_name = data.full_name
    repository.html_url = data.html_url
    repository.description = data.description
    repository.primary_language = data.primary_language
    repository.stars_count = data.stars_count
    repository.forks_count = data.forks_count
    repository.open_issues_count = data.open_issues_count
    repository.watchers_count = data.watchers_count
    repository.github_created_at = data.github_created_at


async def sync_repository(
    db: Session, repository: Repository, client: GitHubClient
) -> tuple[RepositorySnapshot, list[LanguageStat], SyncRun]:
    """Fetch GitHub data and persist a snapshot. Writes nothing on failure."""
    run = SyncRun(
        repository_id=repository.id,
        status=SyncStatus.IN_PROGRESS,
        started_at=_utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        data = await client.fetch_repository(repository.owner, repository.name)
        languages = await client.fetch_languages(data.owner, data.name)
    except GitHubError as exc:
        run.status = SyncStatus.FAILED
        run.finished_at = _utcnow()
        run.error_message = _sanitize(exc.message)
        db.commit()
        logger.info("Sync failed for %s", repository.full_name)
        raise

    captured_at = _utcnow()
    snapshot = RepositorySnapshot(
        repository_id=repository.id,
        stars_count=data.stars_count,
        forks_count=data.forks_count,
        open_issues_count=data.open_issues_count,
        watchers_count=data.watchers_count,
        captured_at=captured_at,
    )
    db.add(snapshot)
    db.flush()

    language_rows = [
        LanguageStat(
            snapshot_id=snapshot.id, language=language, bytes_of_code=bytes_of_code
        )
        for language, bytes_of_code in sorted(
            languages.items(), key=lambda item: item[1], reverse=True
        )
    ]
    db.add_all(language_rows)

    _apply_metadata(repository, data)
    repository.last_synced_at = captured_at

    run.status = SyncStatus.SUCCESS
    run.finished_at = _utcnow()
    run.records_processed = 1 + len(language_rows)
    run.error_message = None

    db.commit()
    db.refresh(snapshot)
    db.refresh(repository)
    db.refresh(run)
    return snapshot, language_rows, run


def recent_sync_runs(db: Session, repository_id: uuid.UUID, limit: int = 20) -> list[SyncRun]:
    return list(
        db.scalars(
            select(SyncRun)
            .where(SyncRun.repository_id == repository_id)
            .order_by(SyncRun.started_at.desc())
            .limit(limit)
        ).all()
    )


def snapshots_for(db: Session, repository_id: uuid.UUID) -> list[RepositorySnapshot]:
    return list(
        db.scalars(
            select(RepositorySnapshot)
            .where(RepositorySnapshot.repository_id == repository_id)
            .order_by(RepositorySnapshot.captured_at)
        ).all()
    )
