import json

def test_register_success(client):
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Donald Banda",
        "email": "donald@example.com",
        "phone": "+265991234567",
        "password": "SecurePassword123!"
    })
    assert response.status_code == 201
    res_data = response.get_json()
    assert res_data["success"] is True
    assert res_data["message"] == "User registered successfully."
    assert "data" in res_data
    assert res_data["data"]["full_name"] == "Donald Banda"
    assert res_data["data"]["email"] == "donald@example.com"
    assert res_data["data"]["phone"] == "+265991234567"
    assert res_data["data"]["user_id"].startswith("usr_")

def test_register_missing_fields(client):
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Donald Banda",
        "email": "",
        "phone": "+265991234567",
        "password": "SecurePassword123!"
    })
    assert response.status_code == 400
    res_data = response.get_json()
    assert res_data["success"] is False
    assert res_data["reason"] == "INVALID_INPUT"

def test_register_duplicate_email(client):
    # Register first user
    client.post("/api/v1/auth/register", json={
        "full_name": "Donald Banda",
        "email": "donald@example.com",
        "phone": "+265991234567",
        "password": "SecurePassword123!"
    })
    # Try duplicate email
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Another Donald",
        "email": "donald@example.com",
        "phone": "+265991234568",
        "password": "SecurePassword123!"
    })
    assert response.status_code == 400
    res_data = response.get_json()
    assert res_data["success"] is False
    assert res_data["reason"] == "EMAIL_ALREADY_EXISTS"

def test_register_duplicate_phone(client):
    # Register first user
    client.post("/api/v1/auth/register", json={
        "full_name": "Donald Banda",
        "email": "donald@example.com",
        "phone": "+265991234567",
        "password": "SecurePassword123!"
    })
    # Try duplicate phone
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Another Donald",
        "email": "another@example.com",
        "phone": "+265991234567",
        "password": "SecurePassword123!"
    })
    assert response.status_code == 400
    res_data = response.get_json()
    assert res_data["success"] is False
    assert res_data["reason"] == "PHONE_ALREADY_EXISTS"

def test_login_success(client):
    # Register user
    client.post("/api/v1/auth/register", json={
        "full_name": "Donald Banda",
        "email": "donald@example.com",
        "phone": "+265991234567",
        "password": "SecurePassword123!"
    })
    # Login
    response = client.post("/api/v1/auth/login", json={
        "email": "donald@example.com",
        "password": "SecurePassword123!"
    })
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    assert "token" in res_data["data"]
    assert res_data["data"]["user"]["email"] == "donald@example.com"
    assert res_data["data"]["user"]["user_id"].startswith("usr_")

def test_login_failure(client):
    # Try login without registering
    response = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "WrongPassword!"
    })
    assert response.status_code == 401
    res_data = response.get_json()
    assert res_data["success"] is False
    assert res_data["reason"] == "INVALID_CREDENTIALS"

def test_get_profile_success(client):
    # Register
    client.post("/api/v1/auth/register", json={
        "full_name": "Donald Banda",
        "email": "donald@example.com",
        "phone": "+265991234567",
        "password": "SecurePassword123!"
    })
    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": "donald@example.com",
        "password": "SecurePassword123!"
    })
    token = login_res.get_json()["data"]["token"]
    
    # Get Profile
    response = client.get("/api/v1/user/profile", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["full_name"] == "Donald Banda"
    assert res_data["data"]["email"] == "donald@example.com"
    assert res_data["data"]["kyc_status"] == "VERIFIED"
    assert "created_at" in res_data["data"]

def test_get_profile_unauthorized(client):
    response = client.get("/api/v1/user/profile", headers={
        "Authorization": "Bearer invalidtoken"
    })
    assert response.status_code == 401
    res_data = response.get_json()
    assert res_data["success"] is False
    assert res_data["reason"] == "UNAUTHORIZED"

def test_update_profile_success(client):
    # Register
    client.post("/api/v1/auth/register", json={
        "full_name": "Donald Banda",
        "email": "donald@example.com",
        "phone": "+265991234567",
        "password": "SecurePassword123!"
    })
    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": "donald@example.com",
        "password": "SecurePassword123!"
    })
    token = login_res.get_json()["data"]["token"]
    
    # Update Profile
    response = client.put("/api/v1/user/profile", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "full_name": "Donald Banda Updated",
        "phone": "+265881234567"
    })
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["full_name"] == "Donald Banda Updated"
    assert res_data["data"]["phone"] == "+265881234567"
    
    # Verify with GET
    get_res = client.get("/api/v1/user/profile", headers={
        "Authorization": f"Bearer {token}"
    })
    assert get_res.get_json()["data"]["full_name"] == "Donald Banda Updated"
    assert get_res.get_json()["data"]["phone"] == "+265881234567"

def test_update_profile_duplicate_phone(client):
    # User 1
    client.post("/api/v1/auth/register", json={
        "full_name": "Donald Banda",
        "email": "donald@example.com",
        "phone": "+265991234567",
        "password": "SecurePassword123!"
    })
    # User 2
    client.post("/api/v1/auth/register", json={
        "full_name": "Second User",
        "email": "second@example.com",
        "phone": "+265991234568",
        "password": "SecurePassword123!"
    })
    
    # Login as User 1
    login_res = client.post("/api/v1/auth/login", json={
        "email": "donald@example.com",
        "password": "SecurePassword123!"
    })
    token = login_res.get_json()["data"]["token"]
    
    # Try updating User 1's phone to User 2's phone
    response = client.put("/api/v1/user/profile", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "phone": "+265991234568"
    })
    assert response.status_code == 400
    res_data = response.get_json()
    assert res_data["success"] is False
    assert res_data["reason"] == "PHONE_ALREADY_EXISTS"
