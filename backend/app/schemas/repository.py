import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

OWNER_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
NAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


class RepositoryCreate(BaseModel):
    owner: str = Field(min_length=1, max_length=39)
    name: str = Field(min_length=1, max_length=100)

    @field_validator("owner")
    @classmethod
    def _check_owner(cls, value: str) -> str:
        value = value.strip()
        if not OWNER_PATTERN.match(value):
            raise ValueError(
                "owner must be a GitHub username or organisation, not a URL or path"
            )
        return value

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        value = value.strip()
        if not NAME_PATTERN.match(value) or value in {".", ".."}:
            raise ValueError(
                "name must be a GitHub repository name, not a URL or path"
            )
        return value


class LanguageStatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language: str
    bytes_of_code: int


class SnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    stars_count: int
    forks_count: int
    open_issues_count: int
    watchers_count: int
    captured_at: datetime


class SyncRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    started_at: datetime
    finished_at: datetime | None
    records_processed: int
    error_message: str | None


class RepositoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner: str
    name: str
    full_name: str
    html_url: str
    description: str | None
    primary_language: str | None
    stars_count: int
    forks_count: int
    open_issues_count: int
    watchers_count: int
    github_created_at: datetime | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RepositoryDetail(RepositoryRead):
    languages: list[LanguageStatRead] = []
    snapshot_count: int = 0


class SyncResult(BaseModel):
    repository: RepositoryRead
    snapshot: SnapshotRead
    languages: list[LanguageStatRead]
    sync_run: SyncRunRead
