from datetime import datetime
from flask import Blueprint, request, jsonify, g
from marshmallow import ValidationError
from backend.app.extensions import db
from backend.app.models.goal import Goal
from backend.app.models.wallet import Wallet
from backend.app.models.transaction import Transaction
from backend.app.utils.auth import token_required
from backend.app.models.notification import Notification
from backend.app.schemas.goal_schema import CreateGoalSchema, DepositGoalSchema

goal_bp = Blueprint("goal", __name__)

_create_goal_schema = CreateGoalSchema()
_deposit_goal_schema = DepositGoalSchema()

def get_or_create_wallet(user_id):
    wallet = db.session.execute(
        db.select(Wallet).filter_by(user_id=user_id)
    ).scalar_one_or_none()
    
    if not wallet:
        wallet = Wallet(user_id=user_id)
        db.session.add(wallet)
        db.session.commit()
        
    return wallet

@goal_bp.route("", methods=["POST"], strict_slashes=False)
@goal_bp.route("/", methods=["POST"], strict_slashes=False)
@token_required
def create_goal():
    user = g.current_user
    data = request.get_json() or {}

    title = data.get("title")
    target_amount = data.get("target_amount")
    target_date_str = data.get("target_date")

    if not title or target_amount is None:
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": "title and target_amount are required."
        }), 400

    title = str(title).strip()

    try:
        target_amount = float(target_amount)
        if target_amount <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": "target_amount must be a positive number."
        }), 400

    target_date = None
    if target_date_str:
        try:
            target_date = datetime.strptime(str(target_date_str).strip(), "%Y-%m-%d").date()
        except ValueError:
            pass

    goal = Goal(
        user_id=user.id,
        title=title,
        target_amount=target_amount,
        current_amount=0.00,
        target_date=target_date,
        status="IN_PROGRESS"
    )

    db.session.add(goal)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Savings goal created successfully.",
        "data": goal.to_dict()
    }), 201

@goal_bp.route("", methods=["GET"], strict_slashes=False)
@goal_bp.route("/", methods=["GET"], strict_slashes=False)
@token_required
def list_goals():
    user = g.current_user

    goals = db.session.execute(
        db.select(Goal).filter_by(user_id=user.id).order_by(Goal.created_at.desc())
    ).scalars().all()

    return jsonify({
        "success": True,
        "message": "Savings goals retrieved successfully.",
        "data": [goal.to_dict() for goal in goals]
    }), 200

@goal_bp.route("/<goal_id>/deposit", methods=["POST"], strict_slashes=False)
@token_required
def deposit_to_goal(goal_id):
    user = g.current_user
    data = request.get_json() or {}

    try:
        validated = _deposit_goal_schema.load(data)
    except ValidationError as err:
        first_msg = next(iter(err.messages.values()))[0]
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": first_msg
        }), 400

    amount = float(validated["amount"])

    goal = db.session.execute(
        db.select(Goal).filter_by(id=goal_id, user_id=user.id)
    ).scalar_one_or_none()

    if not goal:
        return jsonify({
            "success": False,
            "reason": "GOAL_NOT_FOUND",
            "message": "Savings goal not found."
        }), 404

    try:
        # Atomic row-level lock on wallet to prevent concurrent deposit races
        wallet = db.session.execute(
            db.select(Wallet).filter_by(user_id=user.id).with_for_update()
        ).scalar_one_or_none()

        if not wallet:
            wallet = Wallet(user_id=user.id)
            db.session.add(wallet)
            db.session.flush()

        if wallet.balance < amount:
            return jsonify({
                "success": False,
                "reason": "INSUFFICIENT_FUNDS",
                "message": "Your wallet balance is insufficient to complete this deposit."
            }), 400
        wallet.balance -= amount
        goal.current_amount += amount

        if goal.current_amount >= goal.target_amount:
            goal.status = "COMPLETED"

        tx = Transaction(
            sender_id=user.id,
            recipient_id=None,
            amount=amount,
            currency=wallet.currency,
            category="SAVINGS_GOAL",
            status="COMPLETED"
        )

        notif = Notification(
            user_id=user.id,
            title="Goal Deposit",
            type="GOAL",
            message=f"You deposited {wallet.currency} {amount:,.2f} into '{goal.title}'."
        )

        db.session.add(tx)
        db.session.add(notif)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Deposit to savings goal successful.",
            "data": goal.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "reason": "DATABASE_ERROR",
            "message": "An error occurred while processing your deposit."
        }), 500
