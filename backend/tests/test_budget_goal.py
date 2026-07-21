import pytest
from backend.app.extensions import db
from backend.app.models.wallet import Wallet
from backend.app.models.budget import Budget
from backend.app.models.goal import Goal

def register_and_login(client, email="budgetuser@example.com", phone="+265997000001", name="Budget User", password="Password123!"):
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

def test_create_budget_success(client):
    token, user_id = register_and_login(client)
    
    response = client.post("/api/v1/budgets", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "category": "Groceries",
        "limit_amount": 50000.00,
        "period": "MONTHLY"
    })
    
    assert response.status_code == 201
    res_data = response.get_json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["budget_id"].startswith("bdg_")
    assert data["category"] == "Groceries"
    assert data["limit_amount"] == 50000.00
    assert data["spent_amount"] == 0.00
    assert data["remaining_amount"] == 50000.00
    assert data["period"] == "MONTHLY"
    assert data["start_date"] is not None
    assert data["end_date"] is not None

def test_create_weekly_budget(client):
    token, user_id = register_and_login(client, email="weeklyb@example.com", phone="+265997000002")
    
    response = client.post("/api/v1/budgets", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "category": "Entertainment",
        "limit_amount": 15000.00,
        "period": "WEEKLY"
    })
    
    assert response.status_code == 201
    res_data = response.get_json()
    data = res_data["data"]
    assert data["period"] == "WEEKLY"

def test_list_budgets(client):
    token, user_id = register_and_login(client, email="listb@example.com", phone="+265997000003")
    
    client.post("/api/v1/budgets", headers={"Authorization": f"Bearer {token}"}, json={
        "category": "Groceries", "limit_amount": 50000.00, "period": "MONTHLY"
    })
    client.post("/api/v1/budgets", headers={"Authorization": f"Bearer {token}"}, json={
        "category": "Transport", "limit_amount": 20000.00, "period": "MONTHLY"
    })
    
    response = client.get("/api/v1/budgets", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    assert len(res_data["data"]) == 2

def test_create_goal_success(client):
    token, user_id = register_and_login(client, email="goaluser@example.com", phone="+265998000001")
    
    response = client.post("/api/v1/goals", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "title": "Emergency Fund",
        "target_amount": 200000.00,
        "target_date": "2026-12-31"
    })
    
    assert response.status_code == 201
    res_data = response.get_json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["goal_id"].startswith("gol_")
    assert data["title"] == "Emergency Fund"
    assert data["target_amount"] == 200000.00
    assert data["current_amount"] == 0.00
    assert data["progress_percentage"] == 0.0
    assert data["target_date"] == "2026-12-31"
    assert data["status"] == "IN_PROGRESS"

def test_deposit_to_goal_success(client, app):
    token, user_id = register_and_login(client, email="depositgoal@example.com", phone="+265998000002")
    
    # Fund user's wallet
    with app.app_context():
        wallet = db.session.execute(db.select(Wallet).filter_by(user_id=user_id)).scalar_one()
        wallet.balance = 50000.00
        db.session.commit()
        
    goal_resp = client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"}, json={
        "title": "Emergency Fund",
        "target_amount": 200000.00,
        "target_date": "2026-12-31"
    })
    goal_id = goal_resp.get_json()["data"]["goal_id"]
    
    deposit_resp = client.post(f"/api/v1/goals/{goal_id}/deposit", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "amount": 10000.00
    })
    
    assert deposit_resp.status_code == 200
    res_data = deposit_resp.get_json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["goal_id"] == goal_id
    assert data["current_amount"] == 10000.00
    assert data["progress_percentage"] == 5.0
    assert data["status"] == "IN_PROGRESS"
    
    # Verify wallet balance decreased
    w_resp = client.get("/api/v1/wallet", headers={"Authorization": f"Bearer {token}"})
    assert w_resp.get_json()["data"]["balance"] == 40000.00

def test_deposit_to_goal_completion(client, app):
    token, user_id = register_and_login(client, email="completegoal@example.com", phone="+265998000003")
    
    with app.app_context():
        wallet = db.session.execute(db.select(Wallet).filter_by(user_id=user_id)).scalar_one()
        wallet.balance = 100000.00
        db.session.commit()
        
    goal_resp = client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"}, json={
        "title": "New Laptop",
        "target_amount": 50000.00,
        "target_date": "2026-12-31"
    })
    goal_id = goal_resp.get_json()["data"]["goal_id"]
    
    deposit_resp = client.post(f"/api/v1/goals/{goal_id}/deposit", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "amount": 50000.00
    })
    
    assert deposit_resp.status_code == 200
    data = deposit_resp.get_json()["data"]
    assert data["current_amount"] == 50000.00
    assert data["progress_percentage"] == 100.0
    assert data["status"] == "COMPLETED"

def test_deposit_to_goal_insufficient_funds(client):
    token, user_id = register_and_login(client, email="poorgoal@example.com", phone="+265998000004")
    
    goal_resp = client.post("/api/v1/goals", headers={"Authorization": f"Bearer {token}"}, json={
        "title": "House",
        "target_amount": 5000000.00,
        "target_date": "2030-12-31"
    })
    goal_id = goal_resp.get_json()["data"]["goal_id"]
    
    deposit_resp = client.post(f"/api/v1/goals/{goal_id}/deposit", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "amount": 5000.00
    })
    
    assert deposit_resp.status_code == 400
    res_data = deposit_resp.get_json()
    assert res_data["success"] is False
    assert res_data["reason"] == "INSUFFICIENT_FUNDS"
