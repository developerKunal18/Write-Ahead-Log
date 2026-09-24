import pytest
import app as module

@pytest.fixture(autouse=True)
def reset_wal():
    module.wal = module.WriteAheadLog()
    yield

@pytest.fixture
def client():
    module.app.config["TESTING"] = True
    return module.app.test_client()

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"

def test_write_creates_ordered_entries(client):
    first = client.post("/api/write", json={"key": "name", "value": "Kunal"})
    second = client.post("/api/write", json={"key": "city", "value": "Kalyan"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.get_json()["index"] == 1
    assert second.get_json()["index"] == 2

def test_state_updates_after_write(client):
    client.post("/api/write", json={"key": "name", "value": "Kunal"})
    assert client.get("/api/state").get_json()["state"] == {"name": "Kunal"}

def test_latest_value_wins_on_replay(client):
    client.post("/api/write", json={"key": "status", "value": "offline"})
    client.post("/api/write", json={"key": "status", "value": "online"})
    module.wal.state = {}
    client.post("/api/replay")
    assert client.get("/api/state").get_json()["state"]["status"] == "online"

def test_replay_restores_multiple_keys(client):
    client.post("/api/write", json={"key": "a", "value": 1})
    client.post("/api/write", json={"key": "b", "value": 2})
    module.wal.state = {}
    response = client.post("/api/replay")
    assert response.get_json()["state"] == {"a": 1, "b": 2}

def test_missing_value_rejected(client):
    response = client.post("/api/write", json={"key": "name"})
    assert response.status_code == 400
