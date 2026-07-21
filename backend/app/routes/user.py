from flask import Blueprint, request, jsonify, g
from marshmallow import ValidationError
from backend.app.extensions import db
from backend.app.models.users import User
from backend.app.utils.auth import token_required
from backend.app.schemas.user_schema import UpdateProfileSchema, SetPinSchema

user_bp = Blueprint("user", __name__)

_update_profile_schema = UpdateProfileSchema()
_set_pin_schema = SetPinSchema()

@user_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    user = g.current_user
    return jsonify({
        "success": True,
        "message": "Profile retrieved successfully.",
        "data": user.to_dict()
    }), 200

@user_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    user = g.current_user
    data = request.get_json() or {}

    try:
        validated = _update_profile_schema.load(data)
    except ValidationError as err:
        first_msg = next(iter(err.messages.values()))[0]
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": first_msg
        }), 400

    full_name = validated.get("full_name")
    phone = validated.get("phone")

    if full_name is not None:
        user.full_name = str(full_name).strip()

    if phone is not None:
        phone = str(phone).strip()
        # Check if another user has this phone number
        existing_phone = db.session.execute(
            db.select(User).filter(User.phone == phone, User.id != user.id)
        ).scalar_one_or_none()

        if existing_phone:
            return jsonify({
                "success": False,
                "reason": "PHONE_ALREADY_EXISTS",
                "message": "An account with this phone number already exists."
            }), 400

        user.phone = phone

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Profile updated successfully.",
            "data": {
                "user_id": user.id,
                "full_name": user.full_name,
                "phone": user.phone
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "reason": "DATABASE_ERROR",
            "message": "An error occurred while updating your profile."
        }), 500

@user_bp.route("/pin", methods=["POST"])
@token_required
def set_pin():
    """Set or update the user's transaction PIN (stored as an irreversible hash)."""
    user = g.current_user
    data = request.get_json() or {}

    try:
        validated = _set_pin_schema.load(data)
    except ValidationError as err:
        first_msg = next(iter(err.messages.values()))[0]
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": first_msg
        }), 400

    pin = str(validated["pin"]).strip()
    user.set_pin(pin)

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Transaction PIN set successfully.",
            "data": {
                "user_id": user.id,
                "has_pin": True
            }
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({
            "success": False,
            "reason": "DATABASE_ERROR",
            "message": "An error occurred while setting your PIN."
        }), 500
