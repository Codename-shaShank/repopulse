import json
import os
from collections.abc import Iterator

import httpx
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_repopulse.db")
os.environ.setdefault("GITHUB_TOKEN", "")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.api.deps import get_github_client  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Repository  # noqa: E402
from app.services.github import GitHubClient  # noqa: E402

REPO_PAYLOAD = {
    "full_name": "fastapi/fastapi",
    "name": "fastapi",
    "owner": {"login": "fastapi"},
    "html_url": "https://github.com/fastapi/fastapi",
    "description": "FastAPI framework",
    "language": "Python",
    "stargazers_count": 1000,
    "forks_count": 200,
    "open_issues_count": 30,
    "watchers_count": 1000,
    "created_at": "2018-12-08T08:21:47Z",
}

LANGUAGES_PAYLOAD = {"Python": 900000, "HTML": 50000, "CSS": 1000}


class FakeGitHub:
    """Records calls and replays scripted responses for the GitHub endpoints."""

    def __init__(self) -> None:
        self.repo_payload = dict(REPO_PAYLOAD)
        self.languages_payload = dict(LANGUAGES_PAYLOAD)
        self.repo_status = 200
        self.languages_status = 200
        self.headers: dict[str, str] = {}
        self.calls: list[str] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        self.calls.append(path)
        if path.endswith("/languages"):
            return httpx.Response(
                self.languages_status,
                content=json.dumps(self.languages_payload),
                headers={"content-type": "application/json", **self.headers},
            )
        return httpx.Response(
            self.repo_status,
            content=json.dumps(self.repo_payload),
            headers={"content-type": "application/json", **self.headers},
        )

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handler)


@pytest.fixture
def github() -> FakeGitHub:
    return FakeGitHub()


@pytest.fixture
def client(github: FakeGitHub) -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False, future=True
    )

    app = create_app()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    def override_github():
        return GitHubClient(transport=github.transport)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_github_client] = override_github

    # /health talks to the module-level engine, so point it at the test database too.
    import app.main as main_module

    original_engine = main_module.engine
    main_module.engine = engine

    with TestClient(app) as test_client:
        test_client.engine = engine
        test_client.session_factory = TestingSession
        yield test_client

    main_module.engine = original_engine
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def tracked_repository(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/repositories", json={"owner": "fastapi", "name": "fastapi"}
    )
    assert response.status_code == 201, response.text
    return response.json()


def count_rows(client: TestClient, model) -> int:
    from sqlalchemy import func, select

    with client.session_factory() as session:
        return int(session.scalar(select(func.count()).select_from(model)) or 0)


def stored_repository(client: TestClient, repository_id: str) -> Repository | None:
    import uuid as _uuid

    with client.session_factory() as session:
        return session.get(Repository, _uuid.UUID(repository_id))
