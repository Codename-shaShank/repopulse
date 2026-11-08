import uuid
from datetime import datetime

from pydantic import BaseModel


class RecentlySynced(BaseModel):
    id: uuid.UUID
    full_name: str
    last_synced_at: datetime | None
    stars_count: int
    forks_count: int


class AnalyticsSummary(BaseModel):
    tracked_repositories: int
    total_stars: int
    total_forks: int
    total_open_issues: int
    total_snapshots: int
    recently_synced: list[RecentlySynced]


class HealthStatus(BaseModel):
    status: str
    database: str
    version: str
