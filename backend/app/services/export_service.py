import csv
import io
from collections.abc import Iterator
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services import repository_service

SNAPSHOT_HEADER = [
    "snapshot_id",
    "repository_id",
    "repository_full_name",
    "owner",
    "name",
    "stars_count",
    "forks_count",
    "open_issues_count",
    "watchers_count",
    "captured_at",
]

LANGUAGE_HEADER = [
    "repository_full_name",
    "snapshot_id",
    "captured_at",
    "language",
    "bytes_of_code",
]


def _iso(value: datetime | None) -> str:
    """ISO-8601 in UTC, so BigQuery parses the column as a TIMESTAMP."""
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _render(header: list[str], rows: Iterator[list[str]]) -> Iterator[str]:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")

    writer.writerow(header)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for row in rows:
        writer.writerow(row)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


def repository_snapshots_csv(db: Session) -> Iterator[str]:
    def rows() -> Iterator[list[str]]:
        for record in repository_service.snapshot_rows_for_export(db):
            (
                snapshot_id,
                repository_id,
                full_name,
                owner,
                name,
                stars,
                forks,
                issues,
                watchers,
                captured_at,
            ) = record
            yield [
                str(snapshot_id),
                str(repository_id),
                full_name,
                owner,
                name,
                str(stars),
                str(forks),
                str(issues),
                str(watchers),
                _iso(captured_at),
            ]

    return _render(SNAPSHOT_HEADER, rows())


def language_stats_csv(db: Session) -> Iterator[str]:
    def rows() -> Iterator[list[str]]:
        for record in repository_service.language_rows_for_export(db):
            full_name, snapshot_id, captured_at, language, bytes_of_code = record
            yield [
                full_name,
                str(snapshot_id),
                _iso(captured_at),
                language,
                str(bytes_of_code),
            ]

    return _render(LANGUAGE_HEADER, rows())
