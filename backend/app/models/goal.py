from datetime import datetime, timezone, date
import uuid
from backend.app.extensions import db

def generate_goal_id():
    return f"gol_{uuid.uuid4().hex[:9]}"

class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.String(36), primary_key=True, default=generate_goal_id)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, nullable=False, default=0.00)
    target_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="IN_PROGRESS")  # "IN_PROGRESS" or "COMPLETED"
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        target = float(self.target_amount)
        current = float(self.current_amount)
        progress = round((current / target * 100), 1) if target > 0 else 0.0

        return {
            "goal_id": self.id,
            "title": self.title,
            "target_amount": round(target, 2),
            "current_amount": round(current, 2),
            "progress_percentage": min(100.0, progress),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "status": self.status
        }
