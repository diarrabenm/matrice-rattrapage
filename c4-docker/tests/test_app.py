from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


def test_health_returns_200_and_status_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_does_not_depend_on_database(monkeypatch):
    def broken_db():
        raise ConnectionError("db down")

    monkeypatch.setattr(main, "check_database", broken_db)
    assert client.get("/health").status_code == 200


def test_ready_returns_503_when_database_is_down(monkeypatch):
    def broken_db():
        raise ConnectionError("postgresql://matrice:secret@db/matrice refused")

    monkeypatch.setattr(main, "check_database", broken_db)
    response = client.get("/ready")
    assert response.status_code == 503
    assert "secret" not in response.text


def test_ready_returns_200_when_database_is_up(monkeypatch):
    monkeypatch.setattr(main, "check_database", lambda: None)
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}
