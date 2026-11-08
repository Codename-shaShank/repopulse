from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import export_service

router = APIRouter(prefix="/exports", tags=["exports"])


def _csv_response(rows, filename: str) -> StreamingResponse:
    return StreamingResponse(
        rows,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/repository-snapshots.csv")
def repository_snapshots_csv(db: Session = Depends(get_db)) -> StreamingResponse:
    return _csv_response(
        export_service.repository_snapshots_csv(db), "repository_snapshots.csv"
    )


@router.get("/language-stats.csv")
def language_stats_csv(db: Session = Depends(get_db)) -> StreamingResponse:
    return _csv_response(export_service.language_stats_csv(db), "language_stats.csv")
