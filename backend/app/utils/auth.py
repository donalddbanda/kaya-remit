import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify, g, current_app
from backend.app.extensions import db
from backend.app.models.users import User

def generate_token(user_id):
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "iat": datetime.now(timezone.utc),
        "sub": user_id
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256"
    )

def decode_token(token):
    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"]
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return "EXPIRED"
    except jwt.InvalidTokenError:
        return "INVALID"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                
        if not token:
            return jsonify({
                "success": False,
                "reason": "UNAUTHORIZED",
                "message": "Token is missing."
            }), 401
            
        user_id = decode_token(token)
        if user_id in ("EXPIRED", "INVALID"):
            reason = "TOKEN_EXPIRED" if user_id == "EXPIRED" else "INVALID_TOKEN"
            return jsonify({
                "success": False,
                "reason": "UNAUTHORIZED",
                "message": "Token is invalid or expired."
            }), 401
            
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({
                "success": False,
                "reason": "USER_NOT_FOUND",
                "message": "User does not exist."
            }), 401
            
        g.current_user = user
        return f(*args, **kwargs)
    return decorated
