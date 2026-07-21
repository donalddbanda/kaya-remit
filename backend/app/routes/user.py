from flask import Blueprint, request, jsonify, g
from backend.app.extensions import db
from backend.app.models.users import User
from backend.app.utils.auth import token_required

user_bp = Blueprint("user", __name__)

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
    
    full_name = data.get("full_name")
    phone = data.get("phone")
    
    if full_name is not None:
        full_name = str(full_name).strip()
        if not full_name:
            return jsonify({
                "success": False,
                "reason": "INVALID_INPUT",
                "message": "Full name cannot be empty."
            }), 400
        user.full_name = full_name
        
    if phone is not None:
        phone = str(phone).strip()
        if not phone.startswith("+") or len(phone) < 8:
            return jsonify({
                "success": False,
                "reason": "INVALID_INPUT",
                "message": "Phone number must start with '+' followed by country code and local number."
            }), 400
            
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
