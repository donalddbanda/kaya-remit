import pytest
from backend.app.extensions import db
from backend.app.models.wallet import Wallet

def register_and_login(client, email="notifuser@example.com", phone="+265999000001", name="Notif User", password="Password123!"):
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

def test_get_notifications_empty(client):
    token, user_id = register_and_login(client)
    
    response = client.get("/api/v1/notifications", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    assert res_data["data"] == []

def test_get_notifications_unauthorized(client):
    response = client.get("/api/v1/notifications")
    assert response.status_code == 401

def test_transfer_generates_notifications(client, app):
    token1, user_id1 = register_and_login(client, email="notifsender@example.com", phone="+265999000002", name="Sender User")
    token2, user_id2 = register_and_login(client, email="notifrecip@example.com", phone="+265999000003", name="Recipient User")
    
    with app.app_context():
        wallet1 = db.session.execute(db.select(Wallet).filter_by(user_id=user_id1)).scalar_one()
        wallet1.balance = 50000.00
        db.session.commit()
        
    client.post("/api/v1/wallet/transfer", headers={"Authorization": f"Bearer {token1}"}, json={
        "recipient_identifier": "+265999000003",
        "amount": 25000.00,
        "narration": "Test transfer"
    })
    
    # Check sender notification
    resp1 = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token1}"})
    assert resp1.status_code == 200
    notifs1 = resp1.get_json()["data"]
    assert len(notifs1) == 1
    assert notifs1[0]["title"] == "Money Sent"
    assert notifs1[0]["type"] == "TRANSACTION"
    assert notifs1[0]["is_read"] is False
    assert "Recipient User" in notifs1[0]["message"]
    
    # Check recipient notification
    resp2 = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token2}"})
    assert resp2.status_code == 200
    notifs2 = resp2.get_json()["data"]
    assert len(notifs2) == 1
    assert notifs2[0]["title"] == "Money Received"
    assert notifs2[0]["type"] == "TRANSACTION"
    assert notifs2[0]["is_read"] is False
    assert "Sender User" in notifs2[0]["message"]

def test_goal_deposit_generates_notification(client, app):
    token, user_id = register_and_login(client, email="notifgoal@example.com", phone="+265999000004")
    
    with app.app_context():
        wallet = db.session.execute(db.select(Wallet).filter_by(user_id=user_id)).scalar_one()
        wallet.balance = 20000.00
        db.session.commit()
        
    goal_resp = client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"}, json={
        "title": "Vacation Fund",
        "target_amount": 100000.00,
        "target_date": "2026-12-31"
    })
    goal_id = goal_resp.get_json()["data"]["goal_id"]
    
    client.post(f"/api/v1/goals/{goal_id}/deposit", headers={"Authorization": f"Bearer {token}"}, json={
        "amount": 5000.00
    })
    
    resp = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    notifs = resp.get_json()["data"]
    assert len(notifs) == 1
    assert notifs[0]["title"] == "Goal Deposit"
    assert notifs[0]["type"] == "GOAL"
    assert "Vacation Fund" in notifs[0]["message"]

def test_mark_notification_as_read(client, app):
    token1, user_id1 = register_and_login(client, email="markreadsender@example.com", phone="+265999000005")
    token2, user_id2 = register_and_login(client, email="markreadrecip@example.com", phone="+265999000006")
    
    with app.app_context():
        wallet1 = db.session.execute(db.select(Wallet).filter_by(user_id=user_id1)).scalar_one()
        wallet1.balance = 50000.00
        db.session.commit()
        
    client.post("/api/v1/wallet/transfer", headers={"Authorization": f"Bearer {token1}"}, json={
        "recipient_identifier": "+265999000006",
        "amount": 10000.00
    })
    
    notifs_resp = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token1}"})
    notif_id = notifs_resp.get_json()["data"][0]["notification_id"]
    
    read_resp = client.patch(f"/api/v1/notifications/{notif_id}/read", headers={
        "Authorization": f"Bearer {token1}"
    })
    assert read_resp.status_code == 200
    res_data = read_resp.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["is_read"] is True
    
    # Verify notification status updated
    updated_resp = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token1}"})
    assert updated_resp.get_json()["data"][0]["is_read"] is True
