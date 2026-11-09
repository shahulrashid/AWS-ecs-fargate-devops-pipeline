from fastapi.testclient import TestClient

from app.database import InMemoryRepository
from app.main import app, repo

fresh = InMemoryRepository()
app.dependency_overrides[repo] = lambda: fresh
client = TestClient(app)

PAYLOAD = {"title": "Learn AWS DevOps", "description": "Build cloud-native app"}


def setup_function():
    fresh._items.clear()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_readiness():
    assert client.get("/health/ready").status_code == 200


def test_create_and_get():
    created = client.post("/tasks", json=PAYLOAD)
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "pending"
    got = client.get(f"/tasks/{body['task_id']}")
    assert got.status_code == 200
    assert got.json()["title"] == PAYLOAD["title"]


def test_list():
    client.post("/tasks", json=PAYLOAD)
    client.post("/tasks", json={"title": "Second"})
    assert len(client.get("/tasks").json()) == 2


def test_update():
    tid = client.post("/tasks", json=PAYLOAD).json()["task_id"]
    r = client.put(f"/tasks/{tid}", json={"status": "done"})
    assert r.status_code == 200
    assert r.json()["status"] == "done"
    assert r.json()["title"] == PAYLOAD["title"]


def test_delete():
    tid = client.post("/tasks", json=PAYLOAD).json()["task_id"]
    assert client.delete(f"/tasks/{tid}").status_code == 204
    assert client.get(f"/tasks/{tid}").status_code == 404


def test_not_found():
    assert client.get("/tasks/nope").status_code == 404
    assert client.put("/tasks/nope", json={"title": "x"}).status_code == 404
    assert client.delete("/tasks/nope").status_code == 404


def test_validation():
    assert client.post("/tasks", json={"title": ""}).status_code == 422
    assert client.post("/tasks", json={"title": "x", "status": "bogus"}).status_code == 422
