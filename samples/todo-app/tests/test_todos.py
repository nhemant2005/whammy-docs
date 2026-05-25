import pytest
from fastapi.testclient import TestClient
from main import app
from database import db


@pytest.fixture(autouse=True)
def reset_db():
    db.clear()
    db["_next_id"] = 1
    yield


client = TestClient(app)


def test_create_todo():
    resp = client.post("/todos", json={"title": "Buy milk"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Buy milk"
    assert data["done"] is False


def test_list_todos():
    client.post("/todos", json={"title": "Task 1"})
    client.post("/todos", json={"title": "Task 2"})
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_todo_not_found():
    resp = client.get("/todos/999")
    assert resp.status_code == 404


def test_update_todo_done():
    create = client.post("/todos", json={"title": "Walk dog"})
    todo_id = create.json()["id"]
    resp = client.put(f"/todos/{todo_id}", json={"done": True})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_delete_todo():
    create = client.post("/todos", json={"title": "Clean room"})
    todo_id = create.json()["id"]
    resp = client.delete(f"/todos/{todo_id}")
    assert resp.status_code == 204
    assert client.get(f"/todos/{todo_id}").status_code == 404
