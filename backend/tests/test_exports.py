import csv
import io


def _rows(body: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(body)))


def test_snapshot_export_has_headers_and_rows(client, tracked_repository):
    response = client.get("/api/v1/exports/repository-snapshots.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "repository_snapshots.csv" in response.headers["content-disposition"]

    rows = _rows(response.text)
    assert len(rows) == 1
    assert rows[0]["repository_full_name"] == "fastapi/fastapi"
    assert rows[0]["stars_count"] == "1000"
    assert rows[0]["captured_at"].endswith("+00:00")


def test_language_export_has_one_row_per_language(client, tracked_repository):
    response = client.get("/api/v1/exports/language-stats.csv")

    rows = _rows(response.text)
    assert response.status_code == 200
    assert {row["language"] for row in rows} == {"Python", "HTML", "CSS"}
    assert rows[0]["repository_full_name"] == "fastapi/fastapi"
    assert all(row["bytes_of_code"].isdigit() for row in rows)


def test_exports_are_header_only_when_nothing_is_tracked(client):
    snapshots = client.get("/api/v1/exports/repository-snapshots.csv").text
    languages = client.get("/api/v1/exports/language-stats.csv").text

    assert snapshots.strip().splitlines() == [
        "snapshot_id,repository_id,repository_full_name,owner,name,"
        "stars_count,forks_count,open_issues_count,watchers_count,captured_at"
    ]
    assert languages.strip().splitlines() == [
        "repository_full_name,snapshot_id,captured_at,language,bytes_of_code"
    ]


def test_export_grows_with_each_successful_sync(client, tracked_repository):
    client.post(f"/api/v1/repositories/{tracked_repository['id']}/sync")

    rows = _rows(client.get("/api/v1/exports/repository-snapshots.csv").text)

    assert len(rows) == 2
