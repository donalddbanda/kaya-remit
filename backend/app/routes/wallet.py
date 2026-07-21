import math
from flask import Blueprint, request, jsonify, g
from marshmallow import ValidationError
from backend.app.extensions import db
from backend.app.models.users import User
from backend.app.models.wallet import Wallet
from backend.app.models.transaction import Transaction
from backend.app.models.notification import Notification
from backend.app.utils.auth import token_required
from backend.app.schemas.wallet_schema import TransferSchema

wallet_bp = Blueprint("wallet", __name__)

_transfer_schema = TransferSchema()

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

    # Marshmallow validation
    try:
        validated = _transfer_schema.load(data)
    except ValidationError as err:
        first_msg = next(iter(err.messages.values()))[0]
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": first_msg
        }), 400

    recipient_identifier = validated["recipient_identifier"]
    amount = float(validated["amount"])
    currency = validated.get("currency", "MWK")
    category = validated.get("category", "TRANSFER")
    narration = validated.get("narration")
    pin = validated.get("pin")

    # PIN verification if user has configured one
    if user.has_pin:
        if not pin:
            return jsonify({
                "success": False,
                "reason": "PIN_REQUIRED",
                "message": "Transaction PIN is required to complete this transfer."
            }), 403
        if not user.check_pin(pin):
            return jsonify({
                "success": False,
                "reason": "INVALID_PIN",
                "message": "The transaction PIN provided is incorrect."
            }), 403

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

    try:
        # Atomic row-level locks (FOR UPDATE) to prevent race conditions
        sender_wallet = db.session.execute(
            db.select(Wallet).filter_by(user_id=user.id).with_for_update()
        ).scalar_one_or_none()

        if not sender_wallet:
            sender_wallet = Wallet(user_id=user.id)
            db.session.add(sender_wallet)
            db.session.flush()

        recipient_wallet = db.session.execute(
            db.select(Wallet).filter_by(user_id=recipient.id).with_for_update()
        ).scalar_one_or_none()

        if not recipient_wallet:
            recipient_wallet = Wallet(user_id=recipient.id)
            db.session.add(recipient_wallet)
            db.session.flush()

        if sender_wallet.balance < amount:
            return jsonify({
                "success": False,
                "reason": "INSUFFICIENT_FUNDS",
                "message": "Your wallet balance is insufficient to complete this transaction."
            }), 400

        # Atomic debit / credit
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

        # Notifications for sender and recipient
        sender_notif = Notification(
            user_id=user.id,
            title="Money Sent",
            type="TRANSACTION",
            message=f"You sent {currency} {amount:,.2f} to {recipient.full_name}."
        )
        recipient_notif = Notification(
            user_id=recipient.id,
            title="Money Received",
            type="TRANSACTION",
            message=f"You received {currency} {amount:,.2f} from {user.full_name}."
        )

        db.session.add(tx)
        db.session.add(sender_notif)
        db.session.add(recipient_notif)
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
