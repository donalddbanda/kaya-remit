from datetime import datetime, date, timedelta
import calendar
from flask import Blueprint, request, jsonify, g
from marshmallow import ValidationError
from backend.app.extensions import db
from backend.app.models.budget import Budget
from backend.app.utils.auth import token_required
from backend.app.schemas.budget_schema import CreateBudgetSchema

budget_bp = Blueprint("budget", __name__)

_create_budget_schema = CreateBudgetSchema()

def calculate_default_dates(period):
    today = date.today()
    if period.upper() == "WEEKLY":
        start_date = today - timedelta(days=today.weekday())  # Monday of current week
        end_date = start_date + timedelta(days=6)             # Sunday of current week
    else:
        # Default to MONTHLY
        start_date = date(today.year, today.month, 1)
        _, last_day = calendar.monthrange(today.year, today.month)
        end_date = date(today.year, today.month, last_day)
    return start_date, end_date

@budget_bp.route("", methods=["POST"], strict_slashes=False)
@budget_bp.route("/", methods=["POST"], strict_slashes=False)
@token_required
def create_budget():
    user = g.current_user
    data = request.get_json() or {}

    try:
        validated = _create_budget_schema.load(data)
    except ValidationError as err:
        first_msg = next(iter(err.messages.values()))[0]
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": first_msg
        }), 400

    category = validated["category"]
    limit_amount = float(validated["limit_amount"])
    period = validated.get("period", "MONTHLY").upper()
    start_date_str = validated.get("start_date")
    end_date_str = validated.get("end_date")

    start_date = None
    end_date = None

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    if not start_date or not end_date:
        calc_start, calc_end = calculate_default_dates(period)
        if not start_date:
            start_date = calc_start
        if not end_date:
            end_date = calc_end

    budget = Budget(
        user_id=user.id,
        category=category,
        limit_amount=limit_amount,
        spent_amount=0.00,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    db.session.add(budget)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Budget created successfully.",
        "data": budget.to_dict()
    }), 201

@budget_bp.route("", methods=["GET"], strict_slashes=False)
@budget_bp.route("/", methods=["GET"], strict_slashes=False)
@token_required
def list_budgets():
    user = g.current_user

    budgets = db.session.execute(
        db.select(Budget).filter_by(user_id=user.id).order_by(Budget.created_at.desc())
    ).scalars().all()

    return jsonify({
        "success": True,
        "message": "Budgets retrieved successfully.",
        "data": [b.to_dict() for b in budgets]
    }), 200
