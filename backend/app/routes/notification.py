from flask import Blueprint, request, jsonify, g
from backend.app.extensions import db
from backend.app.models.notification import Notification
from backend.app.utils.auth import token_required

notification_bp = Blueprint("notification", __name__)

@notification_bp.route("", methods=["GET"], strict_slashes=False)
@notification_bp.route("/", methods=["GET"], strict_slashes=False)
@token_required
def get_notifications():
    user = g.current_user

    notifications = db.session.execute(
        db.select(Notification).filter_by(user_id=user.id).order_by(Notification.timestamp.desc())
    ).scalars().all()

    return jsonify({
        "success": True,
        "message": "Notifications fetched successfully.",
        "data": [n.to_dict() for n in notifications]
    }), 200

@notification_bp.route("/<notification_id>/read", methods=["PATCH", "PUT"], strict_slashes=False)
@token_required
def mark_as_read(notification_id):
    user = g.current_user

    notification = db.session.execute(
        db.select(Notification).filter_by(id=notification_id, user_id=user.id)
    ).scalar_one_or_none()

    if not notification:
        return jsonify({
            "success": False,
            "reason": "NOTIFICATION_NOT_FOUND",
            "message": "Notification not found."
        }), 404

    notification.read_status = True
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Notification marked as read.",
        "data": {
            "notification_id": notification.id,
            "notif_id": notification.id,
            "is_read": True,
            "read_status": True
        }
    }), 200
