import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_github_client
from app.db.session import get_db
from app.schemas.repository import (
    LanguageStatRead,
    RepositoryCreate,
    RepositoryDetail,
    RepositoryRead,
    SnapshotRead,
    SyncResult,
    SyncRunRead,
)
from app.services import repository_service, sync_service
from app.services.github import GitHubClient

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("", response_model=list[RepositoryRead])
def list_repositories(
    q: str | None = Query(default=None, max_length=200),
    db: Session = Depends(get_db),
) -> list[RepositoryRead]:
    repositories = repository_service.list_repositories(db, q)
    return [RepositoryRead.model_validate(item) for item in repositories]


@router.post("", response_model=RepositoryDetail, status_code=status.HTTP_201_CREATED)
async def add_repository(
    payload: RepositoryCreate,
    db: Session = Depends(get_db),
    client: GitHubClient = Depends(get_github_client),
) -> RepositoryDetail:
    repository = await repository_service.create_repository(
        db, payload.owner, payload.name, client
    )
    return _detail(db, repository)


@router.get("/{repository_id}", response_model=RepositoryDetail)
def get_repository(
    repository_id: uuid.UUID, db: Session = Depends(get_db)
) -> RepositoryDetail:
    repository = sync_service.get_repository(db, repository_id)
    return _detail(db, repository)


@router.post("/{repository_id}/sync", response_model=SyncResult)
async def sync_repository(
    repository_id: uuid.UUID,
    db: Session = Depends(get_db),
    client: GitHubClient = Depends(get_github_client),
) -> SyncResult:
    repository = sync_service.get_repository(db, repository_id)
    snapshot, languages, run = await sync_service.sync_repository(
        db, repository, client
    )
    return SyncResult(
        repository=RepositoryRead.model_validate(repository),
        snapshot=SnapshotRead.model_validate(snapshot),
        languages=[LanguageStatRead.model_validate(item) for item in languages],
        sync_run=SyncRunRead.model_validate(run),
    )


@router.get("/{repository_id}/snapshots", response_model=list[SnapshotRead])
def list_snapshots(
    repository_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[SnapshotRead]:
    sync_service.get_repository(db, repository_id)
    snapshots = sync_service.snapshots_for(db, repository_id)
    return [SnapshotRead.model_validate(item) for item in snapshots]


@router.get("/{repository_id}/sync-runs", response_model=list[SyncRunRead])
def list_sync_runs(
    repository_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[SyncRunRead]:
    sync_service.get_repository(db, repository_id)
    runs = sync_service.recent_sync_runs(db, repository_id, limit)
    return [SyncRunRead.model_validate(item) for item in runs]


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(repository_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    repository_service.delete_repository(db, repository_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _detail(db: Session, repository) -> RepositoryDetail:
    languages = sync_service.latest_languages(db, repository.id)
    detail = RepositoryDetail.model_validate(repository)
    detail.languages = [LanguageStatRead.model_validate(item) for item in languages]
    detail.snapshot_count = sync_service.snapshot_count(db, repository.id)
    return detail
