import math
from flask import Blueprint, request, jsonify, g
from backend.app.extensions import db
from backend.app.models.users import User
from backend.app.models.wallet import Wallet
from backend.app.models.transaction import Transaction
from backend.app.utils.auth import token_required

wallet_bp = Blueprint("wallet", __name__)

def get_or_create_wallet(user_id):
    wallet = db.session.execute(
        db.select(Wallet).filter_by(user_id=user_id)
    ).scalar_one_or_none()
    
    if not wallet:
        wallet = Wallet(user_id=user_id)
        db.session.add(wallet)
        db.session.commit()
        
    return wallet

@wallet_bp.route("", methods=["GET"], strict_slashes=False)
@wallet_bp.route("/", methods=["GET"], strict_slashes=False)
@token_required
def get_wallet():
    user = g.current_user
    wallet = get_or_create_wallet(user.id)
    
    return jsonify({
        "success": True,
        "message": "Wallet details fetched successfully.",
        "data": wallet.to_dict()
    }), 200

@wallet_bp.route("/transfer", methods=["POST"], strict_slashes=False)
@token_required
def transfer_funds():
    user = g.current_user
    data = request.get_json() or {}
    
    recipient_identifier = data.get("recipient_identifier")
    amount = data.get("amount")
    currency = data.get("currency", "MWK")
    category = data.get("category", "TRANSFER")
    narration = data.get("narration")
    
    if not recipient_identifier or amount is None:
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": "recipient_identifier and amount are required."
        }), 400
        
    recipient_identifier = str(recipient_identifier).strip()
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": "Amount must be a positive number."
        }), 400
        
    # Find recipient by phone, email, or user_id
    recipient = db.session.execute(
        db.select(User).filter(
            (User.phone == recipient_identifier) |
            (User.email == recipient_identifier.lower()) |
            (User.id == recipient_identifier)
        )
    ).scalar_one_or_none()
    
    if not recipient:
        return jsonify({
            "success": False,
            "reason": "RECIPIENT_NOT_FOUND",
            "message": "Recipient user not found."
        }), 404

    if recipient.id == user.id:
        return jsonify({
            "success": False,
            "reason": "INVALID_TRANSFER",
            "message": "Cannot transfer money to your own wallet."
        }), 400
        
    sender_wallet = get_or_create_wallet(user.id)
    recipient_wallet = get_or_create_wallet(recipient.id)
    
    if sender_wallet.balance < amount:
        return jsonify({
            "success": False,
            "reason": "INSUFFICIENT_FUNDS",
            "message": "Your wallet balance is insufficient to complete this transaction."
        }), 400
        
    try:
        sender_wallet.balance -= amount
        recipient_wallet.balance += amount
        
        # Single immutable ledger transaction entry
        tx = Transaction(
            sender_id=user.id,
            recipient_id=recipient.id,
            amount=amount,
            currency=currency,
            category=category,
            status="COMPLETED"
        )
        
        db.session.add(tx)
        db.session.commit()
        
        formatted_timestamp = tx.timestamp.isoformat()
        if formatted_timestamp.endswith("+00:00"):
            formatted_timestamp = formatted_timestamp[:-6] + "Z"
        elif not formatted_timestamp.endswith("Z"):
            formatted_timestamp += "Z"
            
        return jsonify({
            "success": True,
            "message": "Transfer processed successfully.",
            "data": {
                "transaction_id": tx.id,
                "txn_id": tx.id,
                "amount": round(float(tx.amount), 2),
                "fee": 0.00,
                "recipient": recipient.full_name,
                "status": "COMPLETED",
                "timestamp": formatted_timestamp
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "reason": "DATABASE_ERROR",
            "message": "An error occurred while processing the transfer."
        }), 500

@wallet_bp.route("/transactions", methods=["GET"], strict_slashes=False)
@token_required
def get_transactions():
    user = g.current_user
    
    try:
        page = max(1, request.args.get("page", 1, type=int))
    except (ValueError, TypeError):
        page = 1
        
    try:
        limit = max(1, request.args.get("limit", 10, type=int))
    except (ValueError, TypeError):
        limit = 10
        
    stmt = db.select(Transaction).filter(
        (Transaction.sender_id == user.id) | (Transaction.recipient_id == user.id)
    ).order_by(Transaction.timestamp.desc())
    
    total_records = db.session.execute(
        db.select(db.func.count()).select_from(stmt.subquery())
    ).scalar() or 0
    
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 1
    offset = (page - 1) * limit
    
    transactions = db.session.execute(
        stmt.offset(offset).limit(limit)
    ).scalars().all()
    
    return jsonify({
        "success": True,
        "message": "Transactions retrieved successfully.",
        "data": {
            "transactions": [tx.to_dict(current_user_id=user.id) for tx in transactions],
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_records": total_records
            }
        }
    }), 200
