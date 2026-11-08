from app.models import LanguageStat, RepositorySnapshot
from tests.conftest import count_rows


def test_sync_creates_exactly_one_snapshot_and_its_language_rows(
    client, tracked_repository, github
):
    github.repo_payload["stargazers_count"] = 1234
    github.languages_payload = {"Python": 950000, "HTML": 60000}

    response = client.post(f"/api/v1/repositories/{tracked_repository['id']}/sync")

    assert response.status_code == 200
    body = response.json()
    assert body["snapshot"]["stars_count"] == 1234
    assert body["repository"]["stars_count"] == 1234
    assert [item["language"] for item in body["languages"]] == ["Python", "HTML"]
    assert body["sync_run"]["status"] == "success"
    assert body["sync_run"]["records_processed"] == 3
    assert count_rows(client, RepositorySnapshot) == 2
    assert count_rows(client, LanguageStat) == 5


def test_failed_sync_records_a_failure_and_writes_no_snapshot(
    client, tracked_repository, github
):
    snapshots_before = count_rows(client, RepositorySnapshot)
    languages_before = count_rows(client, LanguageStat)
    github.repo_status = 500
    github.repo_payload = {"message": "server error"}

    response = client.post(f"/api/v1/repositories/{tracked_repository['id']}/sync")

    assert response.status_code == 503
    assert count_rows(client, RepositorySnapshot) == snapshots_before
    assert count_rows(client, LanguageStat) == languages_before

    runs = client.get(
        f"/api/v1/repositories/{tracked_repository['id']}/sync-runs"
    ).json()
    assert runs[0]["status"] == "failed"
    assert runs[0]["error_message"]
    assert runs[0]["finished_at"] is not None


def test_rate_limited_sync_is_reported_as_429(client, tracked_repository, github):
    github.repo_status = 403
    github.repo_payload = {"message": "API rate limit exceeded"}
    github.headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1760000000"}

    response = client.post(f"/api/v1/repositories/{tracked_repository['id']}/sync")

    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()
    assert response.headers.get("x-ratelimit-reset-at")


def test_a_failed_sync_leaves_earlier_history_intact(
    client, tracked_repository, github
):
    github.repo_status = 500
    client.post(f"/api/v1/repositories/{tracked_repository['id']}/sync")

    snapshots = client.get(
        f"/api/v1/repositories/{tracked_repository['id']}/snapshots"
    ).json()

    assert len(snapshots) == 1
    assert snapshots[0]["stars_count"] == 1000


def test_sync_history_lists_newest_first(client, tracked_repository, github):
    client.post(f"/api/v1/repositories/{tracked_repository['id']}/sync")
    github.repo_status = 500
    client.post(f"/api/v1/repositories/{tracked_repository['id']}/sync")

    runs = client.get(
        f"/api/v1/repositories/{tracked_repository['id']}/sync-runs"
    ).json()

    assert len(runs) == 3
    assert runs[0]["status"] == "failed"
    assert runs[0]["started_at"] >= runs[-1]["started_at"]


def test_sync_returns_404_for_an_unknown_repository(client):
    response = client.post(
        "/api/v1/repositories/8d6c0f6a-0000-4000-8000-000000000000/sync"
    )

    assert response.status_code == 404


def test_transient_failures_are_retried_before_giving_up(client, tracked_repository, github):
    calls_before = len(github.calls)
    github.repo_status = 502

    client.post(f"/api/v1/repositories/{tracked_repository['id']}/sync")

    # One initial attempt plus the configured retries.
    assert len(github.calls) - calls_before == 3
