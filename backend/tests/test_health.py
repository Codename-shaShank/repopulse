def test_health_reports_ok_with_a_reachable_database(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["version"]


def test_health_reports_degraded_when_the_database_is_unreachable(client, monkeypatch):
    import app.main as main_module
    from sqlalchemy import create_engine

    broken = create_engine("postgresql+psycopg://user:pw@127.0.0.1:1/none")
    monkeypatch.setattr(main_module, "engine", broken)

    body = client.get("/health").json()

    assert body["status"] == "degraded"
    assert body["database"] == "unavailable"


def test_health_never_leaks_the_connection_string(client):
    body = client.get("/health").json()

    assert "password" not in str(body).lower()
    assert "postgresql" not in str(body).lower()
