from app.models import LanguageStat, Repository, RepositorySnapshot, SyncRun
from tests.conftest import count_rows


def test_add_repository_stores_metadata_and_first_snapshot(client):
    response = client.post(
        "/api/v1/repositories", json={"owner": "fastapi", "name": "fastapi"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "fastapi/fastapi"
    assert body["stars_count"] == 1000
    assert body["primary_language"] == "Python"
    assert body["snapshot_count"] == 1
    assert body["last_synced_at"] is not None
    assert [item["language"] for item in body["languages"]] == ["Python", "HTML", "CSS"]
    assert count_rows(client, RepositorySnapshot) == 1


def test_add_repository_rejects_a_duplicate(client, tracked_repository):
    response = client.post(
        "/api/v1/repositories", json={"owner": "fastapi", "name": "fastapi"}
    )

    assert response.status_code == 409
    assert "already tracked" in response.json()["detail"]
    assert count_rows(client, Repository) == 1


def test_duplicate_detection_ignores_casing(client, tracked_repository):
    response = client.post(
        "/api/v1/repositories", json={"owner": "FastAPI", "name": "FastAPI"}
    )

    assert response.status_code == 409
    assert count_rows(client, Repository) == 1


def test_add_repository_rejects_invalid_input(client):
    for payload in (
        {"owner": "", "name": "fastapi"},
        {"owner": "fastapi", "name": ""},
        {"owner": "https://github.com/fastapi", "name": "fastapi"},
        {"owner": "fastapi", "name": "../../etc/passwd"},
        {"owner": "fastapi"},
    ):
        response = client.post("/api/v1/repositories", json=payload)
        assert response.status_code == 422, payload

    assert count_rows(client, Repository) == 0


def test_add_repository_returns_404_for_an_unknown_github_repository(client, github):
    github.repo_status = 404
    github.repo_payload = {"message": "Not Found"}

    response = client.post(
        "/api/v1/repositories", json={"owner": "fastapi", "name": "nope"}
    )

    assert response.status_code == 404
    assert count_rows(client, Repository) == 0


def test_list_repositories_supports_search(client, tracked_repository):
    assert len(client.get("/api/v1/repositories").json()) == 1
    assert len(client.get("/api/v1/repositories", params={"q": "fast"}).json()) == 1
    assert len(client.get("/api/v1/repositories", params={"q": "FAST"}).json()) == 1
    assert client.get("/api/v1/repositories", params={"q": "django"}).json() == []


def test_repository_detail_returns_latest_languages(client, tracked_repository):
    response = client.get(f"/api/v1/repositories/{tracked_repository['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "fastapi/fastapi"
    assert body["languages"][0]["language"] == "Python"
    assert body["snapshot_count"] == 1


def test_repository_detail_returns_404_for_an_unknown_id(client):
    response = client.get("/api/v1/repositories/8d6c0f6a-0000-4000-8000-000000000000")

    assert response.status_code == 404


def test_snapshot_history_is_ordered_oldest_first(client, tracked_repository, github):
    github.repo_payload["stargazers_count"] = 1100
    client.post(f"/api/v1/repositories/{tracked_repository['id']}/sync")

    snapshots = client.get(
        f"/api/v1/repositories/{tracked_repository['id']}/snapshots"
    ).json()

    assert [item["stars_count"] for item in snapshots] == [1000, 1100]
    assert snapshots[0]["captured_at"] <= snapshots[1]["captured_at"]


def test_delete_repository_cascades_to_dependent_rows(client, tracked_repository):
    response = client.delete(f"/api/v1/repositories/{tracked_repository['id']}")

    assert response.status_code == 204
    assert count_rows(client, Repository) == 0
    assert count_rows(client, RepositorySnapshot) == 0
    assert count_rows(client, LanguageStat) == 0
    assert count_rows(client, SyncRun) == 0


def test_delete_repository_returns_404_for_an_unknown_id(client):
    response = client.delete(
        "/api/v1/repositories/8d6c0f6a-0000-4000-8000-000000000000"
    )

    assert response.status_code == 404
