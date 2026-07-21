import pytest
from backend.app.extensions import db
from backend.app.models.users import User
from backend.app.models.wallet import Wallet
from backend.app.models.transaction import Transaction

def register_and_login(client, email="user1@example.com", phone="+265991111111", name="User One", password="Password123!"):
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

def test_get_wallet_success(client, app):
    token, user_id = register_and_login(client)
    
    response = client.get("/api/v1/wallet", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    assert res_data["message"] == "Wallet details fetched successfully."
    wallet_data = res_data["data"]
    assert wallet_data["wallet_id"].startswith("wal_")
    assert wallet_data["currency"] == "MWK"
    assert wallet_data["balance"] == 0.00
    assert wallet_data["status"] == "ACTIVE"

def test_get_wallet_unauthorized(client):
    response = client.get("/api/v1/wallet")
    assert response.status_code == 401

def test_transfer_success(client, app):
    token1, user_id1 = register_and_login(client, email="sender@example.com", phone="+265991000001", name="Sender User")
    token2, user_id2 = register_and_login(client, email="recipient@example.com", phone="+265991000002", name="Recipient User")
    
    # Add initial balance to sender's wallet directly in DB
    with app.app_context():
        wallet1 = db.session.execute(db.select(Wallet).filter_by(user_id=user_id1)).scalar_one()
        wallet1.balance = 100000.00
        db.session.commit()
        
    transfer_resp = client.post("/api/v1/wallet/transfer", headers={
        "Authorization": f"Bearer {token1}"
    }, json={
        "recipient_identifier": "+265991000002",
        "amount": 25000.00,
        "currency": "MWK",
        "category": "TRANSFER",
        "narration": "Project expenses"
    })
    
    assert transfer_resp.status_code == 200
    res_data = transfer_resp.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["amount"] == 25000.00
    assert res_data["data"]["recipient"] == "Recipient User"
    assert res_data["data"]["status"] == "COMPLETED"
    assert res_data["data"]["transaction_id"].startswith("tx_")
    assert res_data["data"]["txn_id"].startswith("tx_")
    
    # Verify single immutable ledger entry in DB
    with app.app_context():
        tx = db.session.execute(db.select(Transaction).filter_by(sender_id=user_id1, recipient_id=user_id2)).scalar_one()
        assert tx.amount == 25000.00
        assert tx.category == "TRANSFER"
        assert tx.status == "COMPLETED"
    
    # Check sender balance
    wallet1_resp = client.get("/api/v1/wallet", headers={"Authorization": f"Bearer {token1}"})
    assert wallet1_resp.get_json()["data"]["balance"] == 75000.00
    
    # Check recipient balance
    wallet2_resp = client.get("/api/v1/wallet", headers={"Authorization": f"Bearer {token2}"})
    assert wallet2_resp.get_json()["data"]["balance"] == 25000.00

def test_transfer_insufficient_funds(client, app):
    token1, user_id1 = register_and_login(client, email="poor@example.com", phone="+265992000001", name="Poor Sender")
    token2, user_id2 = register_and_login(client, email="rich@example.com", phone="+265992000002", name="Rich Recipient")
    
    transfer_resp = client.post("/api/v1/wallet/transfer", headers={
        "Authorization": f"Bearer {token1}"
    }, json={
        "recipient_identifier": "+265992000002",
        "amount": 50000.00
    })
    
    assert transfer_resp.status_code == 400
    res_data = transfer_resp.get_json()
    assert res_data["success"] is False
    assert res_data["reason"] == "INSUFFICIENT_FUNDS"

def test_transfer_to_self(client):
    token, user_id = register_and_login(client, email="self@example.com", phone="+265993000001", name="Self User")
    
    transfer_resp = client.post("/api/v1/wallet/transfer", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "recipient_identifier": "+265993000001",
        "amount": 1000.00
    })
    
    assert transfer_resp.status_code == 400
    res_data = transfer_resp.get_json()
    assert res_data["success"] is False
    assert res_data["reason"] == "INVALID_TRANSFER"

def test_transfer_recipient_not_found(client, app):
    token, user_id = register_and_login(client, email="valid@example.com", phone="+265994000001", name="Valid User")
    
    with app.app_context():
        wallet = db.session.execute(db.select(Wallet).filter_by(user_id=user_id)).scalar_one()
        wallet.balance = 50000.00
        db.session.commit()
        
    transfer_resp = client.post("/api/v1/wallet/transfer", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "recipient_identifier": "+265000000000",
        "amount": 1000.00
    })
    
    assert transfer_resp.status_code == 404
    res_data = transfer_resp.get_json()
    assert res_data["success"] is False
    assert res_data["reason"] == "RECIPIENT_NOT_FOUND"

def test_transfer_invalid_amount(client):
    token, user_id = register_and_login(client, email="invalidamt@example.com", phone="+265995000001", name="Amt User")
    
    transfer_resp = client.post("/api/v1/wallet/transfer", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "recipient_identifier": "+265995000002",
        "amount": -500.00
    })
    
    assert transfer_resp.status_code == 400
    res_data = transfer_resp.get_json()
    assert res_data["success"] is False
    assert res_data["reason"] == "INVALID_INPUT"

def test_get_transactions_paginated(client, app):
    token1, user_id1 = register_and_login(client, email="txsender@example.com", phone="+265996000001", name="Tx Sender")
    token2, user_id2 = register_and_login(client, email="txrecip@example.com", phone="+265996000002", name="Tx Recipient")
    
    with app.app_context():
        wallet1 = db.session.execute(db.select(Wallet).filter_by(user_id=user_id1)).scalar_one()
        wallet1.balance = 100000.00
        db.session.commit()
        
    # Perform 2 transfers
    client.post("/api/v1/wallet/transfer", headers={"Authorization": f"Bearer {token1}"}, json={
        "recipient_identifier": "+265996000002",
        "amount": 10000.00,
        "category": "TRANSFER"
    })
    client.post("/api/v1/wallet/transfer", headers={"Authorization": f"Bearer {token1}"}, json={
        "recipient_identifier": "+265996000002",
        "amount": 15000.00,
        "category": "TRANSFER"
    })
    
    # Check sender transactions (DEBIT)
    tx_resp1 = client.get("/api/v1/wallet/transactions?page=1&limit=10", headers={
        "Authorization": f"Bearer {token1}"
    })
    assert tx_resp1.status_code == 200
    data1 = tx_resp1.get_json()["data"]
    assert len(data1["transactions"]) == 2
    assert data1["transactions"][0]["type"] == "DEBIT"
    assert data1["transactions"][0]["sender_id"] == user_id1
    assert data1["transactions"][0]["recipient_id"] == user_id2
    assert data1["transactions"][0]["amount"] == 15000.00
    assert data1["transactions"][0]["recipient_or_sender"] == "Tx Recipient"
    assert data1["pagination"]["total_records"] == 2
    assert data1["pagination"]["current_page"] == 1
    
    # Check recipient transactions (CREDIT)
    tx_resp2 = client.get("/api/v1/wallet/transactions?page=1&limit=10", headers={
        "Authorization": f"Bearer {token2}"
    })
    assert tx_resp2.status_code == 200
    data2 = tx_resp2.get_json()["data"]
    assert len(data2["transactions"]) == 2
    assert data2["transactions"][0]["type"] == "CREDIT"
    assert data2["transactions"][0]["sender_id"] == user_id1
    assert data2["transactions"][0]["recipient_id"] == user_id2
    assert data2["transactions"][0]["amount"] == 15000.00
    assert data2["transactions"][0]["recipient_or_sender"] == "Tx Sender"
