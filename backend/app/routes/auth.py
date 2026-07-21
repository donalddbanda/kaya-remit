from flask import Blueprint, request, jsonify
from backend.app.extensions import db
from backend.app.models.users import User
from backend.app.utils.auth import generate_token
import re

from backend.app.models.wallet import Wallet

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    
    full_name = data.get("full_name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    
    if not all([full_name, email, phone, password]):
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": "All fields (full_name, email, phone, password) are required."
        }), 400
        
    full_name = str(full_name).strip()
    email = str(email).strip().lower()
    phone = str(phone).strip()
    password = str(password)
    
    if not full_name:
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": "Full name cannot be empty."
        }), 400
        
    if not re.match(EMAIL_REGEX, email):
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": "Invalid email address format."
        }), 400
        
    if not phone.startswith("+") or len(phone) < 8:
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": "Phone number must start with '+' followed by country code and local number."
        }), 400
        
    if len(password) < 6:
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": "Password must be at least 6 characters long."
        }), 400

    # Check if email is already taken
    existing_email = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if existing_email:
        return jsonify({
            "success": False,
            "reason": "EMAIL_ALREADY_EXISTS",
            "message": "An account with this email address already exists."
        }), 400

    # Check if phone is already taken
    existing_phone = db.session.execute(db.select(User).filter_by(phone=phone)).scalar_one_or_none()
    if existing_phone:
        return jsonify({
            "success": False,
            "reason": "PHONE_ALREADY_EXISTS",
            "message": "An account with this phone number already exists."
        }), 400

    try:
        user = User(
            full_name=full_name,
            email=email,
            phone=phone
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        wallet = Wallet(user_id=user.id)
        db.session.add(wallet)

        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "User registered successfully.",
            "data": {
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "reason": "DATABASE_ERROR",
            "message": "An error occurred while creating your account."
        }), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": "Email and password are required."
        }), 400
        
    email = str(email).strip().lower()
    password = str(password)
    
    user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if not user or not user.check_password(password):
        return jsonify({
            "success": False,
            "reason": "INVALID_CREDENTIALS",
            "message": "The email or password provided is incorrect."
        }), 401
        
    token = generate_token(user.id)
    
    return jsonify({
        "success": True,
        "message": "Login successful.",
        "data": {
            "token": token,
            "user": {
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email
            }
        }
    }), 200
