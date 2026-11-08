def test_summary_is_empty_before_anything_is_tracked(client):
    body = client.get("/api/v1/analytics/summary").json()

    assert body == {
        "tracked_repositories": 0,
        "total_stars": 0,
        "total_forks": 0,
        "total_open_issues": 0,
        "total_snapshots": 0,
        "recently_synced": [],
    }


def test_summary_aggregates_latest_metrics(client, tracked_repository, github):
    github.repo_payload = dict(
        github.repo_payload,
        full_name="tiangolo/typer",
        name="typer",
        owner={"login": "tiangolo"},
        stargazers_count=500,
        forks_count=50,
        open_issues_count=10,
    )
    client.post("/api/v1/repositories", json={"owner": "tiangolo", "name": "typer"})

    body = client.get("/api/v1/analytics/summary").json()

    assert body["tracked_repositories"] == 2
    assert body["total_stars"] == 1500
    assert body["total_forks"] == 250
    assert body["total_open_issues"] == 40
    assert body["total_snapshots"] == 2
    assert len(body["recently_synced"]) == 2
    assert {item["full_name"] for item in body["recently_synced"]} == {
        "fastapi/fastapi",
        "tiangolo/typer",
    }


def test_summary_reflects_a_deletion(client, tracked_repository):
    client.delete(f"/api/v1/repositories/{tracked_repository['id']}")

    body = client.get("/api/v1/analytics/summary").json()

    assert body["tracked_repositories"] == 0
    assert body["total_stars"] == 0
    assert body["total_snapshots"] == 0
