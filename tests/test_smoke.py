from fastapi.testclient import TestClient

from app.backend.main import app


client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_seed_projects_and_pmo_requirements():
    projects = client.get("/api/projects")
    assert projects.status_code == 200
    assert len(projects.json()) == 4

    reqs = client.get("/api/requirements?project_id=VCL-DEV-PMO-002")
    assert reqs.status_code == 200
    assert len(reqs.json()) == 10


def test_round_trip_routes():
    assert client.get("/api/issues").status_code == 200
    assert client.get("/api/uat").status_code == 200
    assert client.get("/api/agent/log").status_code == 200
    assert client.get("/api/sync/status").status_code == 200
