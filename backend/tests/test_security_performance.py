import pytest
from backend.app.extensions import db
from backend.app.models.users import User
from backend.app.models.wallet import Wallet

def register_and_login(client, email="secuser@example.com", phone="+265981000001", name="Sec User", password="Password123!"):
    reg_resp = client.post("/api/v1/auth/register", json={
        "full_name": name,
        "email": email,
        "phone": phone,
        "password": password
    })
    assert reg_resp.status_code == 201
    login_resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_resp.status_code == 200
    token = login_resp.get_json()["data"]["token"]
    user_id = login_resp.get_json()["data"]["user"]["user_id"]
    return token, user_id

# --- Marshmallow Input Validation ---

def test_register_invalid_email(client):
    resp = client.post("/api/v1/auth/register", json={
        "full_name": "Test",
        "email": "not-an-email",
        "phone": "+265991000000",
        "password": "SecurePass1!"
    })
    assert resp.status_code == 400
    assert resp.get_json()["reason"] == "INVALID_INPUT"

def test_register_short_password(client):
    resp = client.post("/api/v1/auth/register", json={
        "full_name": "Test",
        "email": "short@example.com",
        "phone": "+265991000001",
        "password": "abc"
    })
    assert resp.status_code == 400
    assert resp.get_json()["reason"] == "INVALID_INPUT"

def test_register_missing_field(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "missing@example.com",
        "password": "Password123!"
    })
    assert resp.status_code == 400
    assert resp.get_json()["reason"] == "INVALID_INPUT"

def test_budget_invalid_amount(client):
    token, _ = register_and_login(client, email="budgetval@example.com", phone="+265981000002")
    resp = client.post("/api/v1/budgets", headers={"Authorization": f"Bearer {token}"}, json={
        "category": "Groceries",
        "limit_amount": -500.00,
        "period": "MONTHLY"
    })
    assert resp.status_code == 400
    assert resp.get_json()["reason"] == "INVALID_INPUT"

def test_transfer_invalid_amount_marshmallow(client):
    token, _ = register_and_login(client, email="transferval@example.com", phone="+265981000003")
    resp = client.post("/api/v1/wallet/transfer", headers={"Authorization": f"Bearer {token}"}, json={
        "recipient_identifier": "+265981000004",
        "amount": -100.00
    })
    assert resp.status_code == 400
    assert resp.get_json()["reason"] == "INVALID_INPUT"

# --- Security Headers ---

def test_security_headers_present(client):
    resp = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "WrongPassword"
    })
    assert "Strict-Transport-Security" in resp.headers
    assert resp.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-XSS-Protection"] == "1; mode=block"

# --- PIN Security ---

def test_set_pin_success(client):
    token, user_id = register_and_login(client, email="pinuser@example.com", phone="+265981000005")
    resp = client.post("/api/v1/user/pin", headers={"Authorization": f"Bearer {token}"}, json={
        "pin": "1234"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["has_pin"] is True

def test_set_pin_invalid_non_numeric(client):
    token, _ = register_and_login(client, email="pinval@example.com", phone="+265981000006")
    resp = client.post("/api/v1/user/pin", headers={"Authorization": f"Bearer {token}"}, json={
        "pin": "abcd"
    })
    assert resp.status_code == 400
    assert resp.get_json()["reason"] == "INVALID_INPUT"

def test_set_pin_invalid_length(client):
    token, _ = register_and_login(client, email="pinlen@example.com", phone="+265981000007")
    resp = client.post("/api/v1/user/pin", headers={"Authorization": f"Bearer {token}"}, json={
        "pin": "12"
    })
    assert resp.status_code == 400
    assert resp.get_json()["reason"] == "INVALID_INPUT"

def test_transfer_requires_pin_when_set(client, app):
    token1, user_id1 = register_and_login(client, email="pinnedsender@example.com", phone="+265981000008")
    _, user_id2 = register_and_login(client, email="pinnedrecip@example.com", phone="+265981000009")

    # Set PIN
    client.post("/api/v1/user/pin", headers={"Authorization": f"Bearer {token1}"}, json={"pin": "5678"})

    # Fund wallet
    with app.app_context():
        wallet = db.session.execute(db.select(Wallet).filter_by(user_id=user_id1)).scalar_one()
        wallet.balance = 50000.00
        db.session.commit()

    # Transfer without PIN → should be rejected
    resp_no_pin = client.post("/api/v1/wallet/transfer", headers={"Authorization": f"Bearer {token1}"}, json={
        "recipient_identifier": "+265981000009",
        "amount": 1000.00
    })
    assert resp_no_pin.status_code == 403
    assert resp_no_pin.get_json()["reason"] == "PIN_REQUIRED"

    # Transfer with wrong PIN → should be rejected
    resp_wrong_pin = client.post("/api/v1/wallet/transfer", headers={"Authorization": f"Bearer {token1}"}, json={
        "recipient_identifier": "+265981000009",
        "amount": 1000.00,
        "pin": "9999"
    })
    assert resp_wrong_pin.status_code == 403
    assert resp_wrong_pin.get_json()["reason"] == "INVALID_PIN"

    # Transfer with correct PIN → should succeed
    resp_ok = client.post("/api/v1/wallet/transfer", headers={"Authorization": f"Bearer {token1}"}, json={
        "recipient_identifier": "+265981000009",
        "amount": 1000.00,
        "pin": "5678"
    })
    assert resp_ok.status_code == 200
    assert resp_ok.get_json()["data"]["status"] == "COMPLETED"

def test_pin_not_exposed_in_profile(client, app):
    """Ensure transaction_pin_hash is never returned in any profile response."""
    token, user_id = register_and_login(client, email="pinexposed@example.com", phone="+265981000010")
    client.post("/api/v1/user/pin", headers={"Authorization": f"Bearer {token}"}, json={"pin": "1234"})

    resp = client.get("/api/v1/user/profile", headers={"Authorization": f"Bearer {token}"})
    profile = resp.get_json()["data"]
    assert "transaction_pin_hash" not in profile
    assert "pin" not in profile
