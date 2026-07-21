from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from backend.app.extensions import db
from backend.app.models.users import User
from backend.app.models.wallet import Wallet
from backend.app.utils.auth import generate_token
from backend.app.schemas.auth_schema import RegisterSchema, LoginSchema
import re

auth_bp = Blueprint("auth", __name__)

_register_schema = RegisterSchema()
_login_schema = LoginSchema()

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    try:
        validated = _register_schema.load(data)
    except ValidationError as err:
        first_msg = next(iter(err.messages.values()))[0]
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": first_msg
        }), 400

    full_name = str(validated["full_name"]).strip()
    email = str(validated["email"]).strip().lower()
    phone = str(validated["phone"]).strip()
    password = str(validated["password"])

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

    try:
        validated = _login_schema.load(data)
    except ValidationError as err:
        first_msg = next(iter(err.messages.values()))[0]
        return jsonify({
            "success": False,
            "reason": "INVALID_INPUT",
            "message": first_msg
        }), 400

    email = str(validated["email"]).strip().lower()
    password = str(validated["password"])

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
