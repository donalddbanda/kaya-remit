from datetime import datetime, timezone
import uuid
from backend.app.extensions import db

def generate_notification_id():
    return f"notif_{uuid.uuid4().hex[:9]}"

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.String(36), primary_key=True, default=generate_notification_id)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False, default="Notification")
    type = db.Column(db.String(50), nullable=False, default="SYSTEM")  # "TRANSACTION", "GOAL", "SYSTEM"
    message = db.Column(db.Text, nullable=False)
    read_status = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        formatted_date = self.timestamp.isoformat()
        if formatted_date.endswith("+00:00"):
            formatted_date = formatted_date[:-6] + "Z"
        elif not formatted_date.endswith("Z"):
            formatted_date += "Z"

        return {
            "notification_id": self.id,
            "notif_id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "type": self.type,
            "message": self.message,
            "is_read": self.read_status,
            "read_status": self.read_status,
            "timestamp": formatted_date,
            "created_at": formatted_date
        }
