"""CivicLens — Pytest suite (used in Jenkins Test stage)"""
import os
import tempfile
import pytest

# Use a temp DB for tests
@pytest.fixture
def client():
    import app as app_module
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    app_module.DATABASE = db_path
    app_module.UPLOAD_FOLDER = tempfile.mkdtemp()
    app_module.app.config["UPLOAD_FOLDER"] = app_module.UPLOAD_FOLDER
    app_module.init_db()
    app_module.app.config["TESTING"] = True
    app_module.app.config["DATABASE"] = db_path
    with app_module.app.test_client() as c:
        yield c
    os.close(db_fd)
    try:
        os.remove(db_path)
    except OSError:
        pass


def valid_payload(**overrides):
    data = dict(
        title="Large pothole on MG Road",
        description="Deep pothole near signal, dangerous for bikes. Needs urgent repair.",
        category="pothole",
        latitude="18.5204",
        longitude="73.8567",
        address="MG Road, Pune",
    )
    data.update(overrides)
    return data


# ── Health ──
def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


# ── Create ──
def test_create_issue_success(client):
    res = client.post("/api/issues", json=valid_payload())
    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "Large pothole on MG Road"
    assert body["status"] == "Open"
    assert body["upvotes"] == 0


def test_create_issue_validation_title(client):
    res = client.post("/api/issues", json=valid_payload(title="ab"))
    assert res.status_code == 400
    assert any("Title" in e for e in res.get_json()["errors"])


def test_create_issue_validation_category(client):
    res = client.post("/api/issues", json=valid_payload(category="invalid"))
    assert res.status_code == 400


def test_create_issue_validation_coords(client):
    res = client.post("/api/issues", json=valid_payload(latitude="999", longitude="999"))
    assert res.status_code == 400


# ── List & Filter ──
def test_list_issues(client):
    client.post("/api/issues", json=valid_payload())
    client.post("/api/issues", json=valid_payload(title="Garbage pile at market", category="garbage"))
    res = client.get("/api/issues")
    assert res.status_code == 200
    assert len(res.get_json()) == 2


def test_filter_by_category(client):
    client.post("/api/issues", json=valid_payload(category="pothole"))
    client.post("/api/issues", json=valid_payload(title="Garbage overflowing", category="garbage"))
    res = client.get("/api/issues?category=pothole")
    assert all(i["category"] == "pothole" for i in res.get_json())


def test_search(client):
    client.post("/api/issues", json=valid_payload(title="Unique Search Term XYZ"))
    res = client.get("/api/issues?search=XYZ")
    assert len(res.get_json()) == 1


# ── Status update ──
def test_update_status(client):
    created = client.post("/api/issues", json=valid_payload()).get_json()
    res = client.patch(f"/api/issues/{created['id']}/status", json={"status": "In-Progress"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "In-Progress"

    res2 = client.patch(f"/api/issues/{created['id']}/status", json={"status": "Resolved"})
    assert res2.get_json()["status"] == "Resolved"


def test_update_status_invalid(client):
    created = client.post("/api/issues", json=valid_payload()).get_json()
    res = client.patch(f"/api/issues/{created['id']}/status", json={"status": "Done"})
    assert res.status_code == 400


# ── Upvote ──
def test_upvote(client):
    created = client.post("/api/issues", json=valid_payload()).get_json()
    res = client.post(f"/api/issues/{created['id']}/upvote")
    assert res.status_code == 200
    assert res.get_json()["upvotes"] == 1
    res2 = client.post(f"/api/issues/{created['id']}/upvote")
    assert res2.get_json()["upvotes"] == 2


# ── Delete ──
def test_delete(client):
    created = client.post("/api/issues", json=valid_payload()).get_json()
    res = client.delete(f"/api/issues/{created['id']}")
    assert res.status_code == 200
    res2 = client.get(f"/api/issues/{created['id']}")
    assert res2.status_code == 404


# ── Stats ──
def test_stats(client):
    client.post("/api/issues", json=valid_payload())
    res = client.get("/api/stats")
    assert res.status_code == 200
    assert res.get_json()["total"] == 1
    assert res.get_json()["open"] == 1


# ── Get single ──
def test_get_single_not_found(client):
    res = client.get("/api/issues/doesnotexist")
    assert res.status_code == 404
