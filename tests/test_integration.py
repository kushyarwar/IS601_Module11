"""
Integration tests — require a real database (SQLite locally, PostgreSQL in CI).
Tests cover user creation, calculation creation, DB correctness, and error cases.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_user(client, username="testuser", email=None):
    if email is None:
        email = f"{username}@example.com"
    res = client.post("/users/", json={
        "username": username,
        "email": email,
        "password": "pass123",
    })
    assert res.status_code == 201
    return res.json()["id"]


# ── User tests ────────────────────────────────────────────────────────────────

def test_create_user_success(client):
    res = client.post("/users/", json={
        "username": "bob",
        "email": "bob@example.com",
        "password": "pass123",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "bob"
    assert data["email"] == "bob@example.com"
    assert "id" in data


def test_response_omits_password(client):
    res = client.post("/users/", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "supersecret",
    })
    data = res.json()
    assert "password" not in data
    assert "password_hash" not in data


def test_duplicate_username_rejected(client):
    client.post("/users/", json={"username": "charlie", "email": "c1@example.com", "password": "p"})
    res = client.post("/users/", json={"username": "charlie", "email": "c2@example.com", "password": "p"})
    assert res.status_code == 400


def test_duplicate_email_rejected(client):
    client.post("/users/", json={"username": "dave1", "email": "dave@example.com", "password": "p"})
    res = client.post("/users/", json={"username": "dave2", "email": "dave@example.com", "password": "p"})
    assert res.status_code == 400


def test_invalid_email_format_rejected(client):
    res = client.post("/users/", json={
        "username": "eve",
        "email": "not-an-email",
        "password": "pass",
    })
    assert res.status_code == 422


def test_get_user_by_id(client):
    user_id = _create_user(client, "frank")
    res = client.get(f"/users/{user_id}")
    assert res.status_code == 200
    assert res.json()["username"] == "frank"


def test_get_nonexistent_user_returns_404(client):
    res = client.get("/users/99999")
    assert res.status_code == 404


def test_delete_user(client):
    user_id = _create_user(client, "todelete")
    assert client.delete(f"/users/{user_id}").status_code == 204
    assert client.get(f"/users/{user_id}").status_code == 404


# ── Calculation creation ──────────────────────────────────────────────────────

def test_create_add_calculation(client):
    user_id = _create_user(client, "calc_user1")
    res = client.post("/calculations/", json={"a": 10, "b": 5, "type": "Add", "user_id": user_id})
    assert res.status_code == 201
    data = res.json()
    assert data["result"] == 15.0
    assert data["type"] == "Add"
    assert data["a"] == 10.0
    assert data["b"] == 5.0


def test_create_sub_calculation(client):
    user_id = _create_user(client, "calc_user2")
    res = client.post("/calculations/", json={"a": 20, "b": 8, "type": "Sub", "user_id": user_id})
    assert res.status_code == 201
    assert res.json()["result"] == 12.0


def test_create_multiply_calculation(client):
    user_id = _create_user(client, "calc_user3")
    res = client.post("/calculations/", json={"a": 6, "b": 7, "type": "Multiply", "user_id": user_id})
    assert res.status_code == 201
    assert res.json()["result"] == 42.0


def test_create_divide_calculation(client):
    user_id = _create_user(client, "calc_user4")
    res = client.post("/calculations/", json={"a": 15, "b": 3, "type": "Divide", "user_id": user_id})
    assert res.status_code == 201
    assert res.json()["result"] == 5.0


# ── DB correctness ────────────────────────────────────────────────────────────

def test_calculation_stored_in_db(client):
    user_id = _create_user(client, "db_user")
    create_res = client.post("/calculations/", json={"a": 4, "b": 4, "type": "Add", "user_id": user_id})
    calc_id = create_res.json()["id"]
    fetch_res = client.get(f"/calculations/{calc_id}")
    assert fetch_res.status_code == 200
    stored = fetch_res.json()
    assert stored["a"] == 4.0
    assert stored["b"] == 4.0
    assert stored["type"] == "Add"
    assert stored["result"] == 8.0
    assert stored["user_id"] == user_id


def test_calculation_has_timestamp(client):
    user_id = _create_user(client, "ts_user")
    res = client.post("/calculations/", json={"a": 1, "b": 1, "type": "Add", "user_id": user_id})
    assert res.json().get("timestamp") is not None


def test_list_calculations(client):
    user_id = _create_user(client, "list_user")
    client.post("/calculations/", json={"a": 1, "b": 2, "type": "Add", "user_id": user_id})
    client.post("/calculations/", json={"a": 3, "b": 4, "type": "Multiply", "user_id": user_id})
    res = client.get("/calculations/")
    assert res.status_code == 200
    assert len(res.json()) >= 2


# ── Error cases ───────────────────────────────────────────────────────────────

def test_divide_by_zero_rejected(client):
    user_id = _create_user(client, "div_user")
    res = client.post("/calculations/", json={"a": 10, "b": 0, "type": "Divide", "user_id": user_id})
    assert res.status_code == 422


def test_invalid_type_rejected(client):
    user_id = _create_user(client, "type_user")
    res = client.post("/calculations/", json={"a": 5, "b": 3, "type": "Power", "user_id": user_id})
    assert res.status_code == 422


def test_invalid_user_id_rejected(client):
    res = client.post("/calculations/", json={"a": 5, "b": 3, "type": "Add", "user_id": 99999})
    assert res.status_code == 404


def test_get_nonexistent_calculation_returns_404(client):
    res = client.get("/calculations/99999")
    assert res.status_code == 404


def test_delete_calculation(client):
    user_id = _create_user(client, "del_calc_user")
    create_res = client.post("/calculations/", json={"a": 2, "b": 2, "type": "Multiply", "user_id": user_id})
    calc_id = create_res.json()["id"]
    assert client.delete(f"/calculations/{calc_id}").status_code == 204
    assert client.get(f"/calculations/{calc_id}").status_code == 404


def test_delete_user_cascades_calculations(client):
    user_id = _create_user(client, "cascade_user")
    create_res = client.post("/calculations/", json={"a": 5, "b": 5, "type": "Add", "user_id": user_id})
    calc_id = create_res.json()["id"]
    client.delete(f"/users/{user_id}")
    assert client.get(f"/calculations/{calc_id}").status_code == 404


# ── Health check ──────────────────────────────────────────────────────────────

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
