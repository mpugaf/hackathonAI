def test_login_success(client):
    response = client.post("/auth/login", json={"email": "analista@tcs.com", "password": "analista123"})
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client):
    response = client.post("/auth/login", json={"email": "analista@tcs.com", "password": "bad"})
    assert response.status_code == 401


def test_login_user_not_found(client):
    response = client.post("/auth/login", json={"email": "nadie@tcs.com", "password": "bad"})
    assert response.status_code == 401


def test_logout_valid_token(client, analista_token):
    response = client.post("/auth/logout", headers={"Authorization": f"Bearer {analista_token}"})
    assert response.status_code == 200


def test_logout_no_token(client):
    response = client.post("/auth/logout")
    assert response.status_code == 401
