"""API smoke tests via FastAPI TestClient. These never call OpenAI: /report reads
the committed fixture, and the live-run guard is tested for the no-key path."""
import os
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_harness.db")
from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert "live_enabled" in r.json()


def test_report_has_all_screens_data():
    r = client.get("/api/report")
    assert r.status_code == 200
    d = r.json()
    for key in ["metrics", "counters", "verdict", "comparison", "heatmap",
                "clusters", "proposals", "policy", "personas", "transcript", "judge"]:
        assert key in d, f"missing {key}"
    assert len(d["personas"]) == 8
    assert d["verdict"]["label"] in ("REAL_PROGRESS", "MIXED", "LIKELY_GAMING")


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "Red Team Harness" in r.text


def test_live_run_rejects_when_no_usable_key():
    r = client.post("/api/run", json={"n_skills": 1, "n_turns": 1, "api_key": "not-a-key"})
    assert r.status_code == 400


def test_runs_list_empty_ok():
    r = client.get("/api/runs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
