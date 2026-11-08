import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import DuplicateError, GitHubError
from app.models import LanguageStat, Repository, RepositorySnapshot, SyncRun
from app.services import sync_service
from app.services.github import GitHubClient


def find_by_full_name(db: Session, full_name: str) -> Repository | None:
    return db.scalars(
        select(Repository).where(func.lower(Repository.full_name) == full_name.lower())
    ).first()


def list_repositories(db: Session, q: str | None = None) -> list[Repository]:
    statement = select(Repository)
    if q:
        pattern = f"%{q.strip().lower()}%"
        statement = statement.where(
            or_(
                func.lower(Repository.owner).like(pattern),
                func.lower(Repository.name).like(pattern),
                func.lower(Repository.full_name).like(pattern),
            )
        )
    statement = statement.order_by(Repository.full_name)
    return list(db.scalars(statement).all())


async def create_repository(
    db: Session, owner: str, name: str, client: GitHubClient
) -> Repository:
    """Validate against GitHub, store the repository, then run its first sync."""
    if find_by_full_name(db, f"{owner}/{name}") is not None:
        raise DuplicateError(f"{owner}/{name} is already tracked")

    data = await client.fetch_repository(owner, name)

    if find_by_full_name(db, data.full_name) is not None:
        raise DuplicateError(f"{data.full_name} is already tracked")

    repository = Repository(
        id=uuid.uuid4(),
        owner=data.owner,
        name=data.name,
        full_name=data.full_name,
        html_url=data.html_url,
        description=data.description,
        primary_language=data.primary_language,
        stars_count=data.stars_count,
        forks_count=data.forks_count,
        open_issues_count=data.open_issues_count,
        watchers_count=data.watchers_count,
        github_created_at=data.github_created_at,
    )
    db.add(repository)
    db.commit()
    db.refresh(repository)

    try:
        await sync_service.sync_repository(db, repository, client)
    except GitHubError:
        # The repository is tracked and the failure is recorded as a sync run;
        # the user can retry with Sync now rather than re-adding it.
        db.refresh(repository)

    return repository


def delete_repository(db: Session, repository_id: uuid.UUID) -> None:
    repository = sync_service.get_repository(db, repository_id)
    db.delete(repository)
    db.commit()


def analytics_summary(db: Session) -> dict:
    tracked = int(db.scalar(select(func.count()).select_from(Repository)) or 0)
    totals = db.execute(
        select(
            func.coalesce(func.sum(Repository.stars_count), 0),
            func.coalesce(func.sum(Repository.forks_count), 0),
            func.coalesce(func.sum(Repository.open_issues_count), 0),
        )
    ).one()
    total_snapshots = int(
        db.scalar(select(func.count()).select_from(RepositorySnapshot)) or 0
    )

    recent = db.scalars(
        select(Repository)
        .where(Repository.last_synced_at.is_not(None))
        .order_by(Repository.last_synced_at.desc())
        .limit(5)
    ).all()

    return {
        "tracked_repositories": tracked,
        "total_stars": int(totals[0]),
        "total_forks": int(totals[1]),
        "total_open_issues": int(totals[2]),
        "total_snapshots": total_snapshots,
        "recently_synced": [
            {
                "id": repository.id,
                "full_name": repository.full_name,
                "last_synced_at": repository.last_synced_at,
                "stars_count": repository.stars_count,
                "forks_count": repository.forks_count,
            }
            for repository in recent
        ],
    }


def language_rows_for_export(db: Session):
    return db.execute(
        select(
            Repository.full_name,
            RepositorySnapshot.id,
            RepositorySnapshot.captured_at,
            LanguageStat.language,
            LanguageStat.bytes_of_code,
        )
        .join(RepositorySnapshot, RepositorySnapshot.repository_id == Repository.id)
        .join(LanguageStat, LanguageStat.snapshot_id == RepositorySnapshot.id)
        .order_by(Repository.full_name, RepositorySnapshot.captured_at, LanguageStat.language)
    )


def snapshot_rows_for_export(db: Session):
    return db.execute(
        select(
            RepositorySnapshot.id,
            Repository.id,
            Repository.full_name,
            Repository.owner,
            Repository.name,
            RepositorySnapshot.stars_count,
            RepositorySnapshot.forks_count,
            RepositorySnapshot.open_issues_count,
            RepositorySnapshot.watchers_count,
            RepositorySnapshot.captured_at,
        )
        .join(Repository, Repository.id == RepositorySnapshot.repository_id)
        .order_by(Repository.full_name, RepositorySnapshot.captured_at)
    )


def last_sync_run(db: Session, repository_id: uuid.UUID) -> SyncRun | None:
    return db.scalars(
        select(SyncRun)
        .where(SyncRun.repository_id == repository_id)
        .order_by(SyncRun.started_at.desc())
        .limit(1)
    ).first()
