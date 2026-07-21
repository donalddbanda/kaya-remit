from datetime import datetime, timezone, date
import uuid
from backend.app.extensions import db

def generate_budget_id():
    return f"bdg_{uuid.uuid4().hex[:9]}"

class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.String(36), primary_key=True, default=generate_budget_id)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False)
    limit_amount = db.Column(db.Float, nullable=False)
    spent_amount = db.Column(db.Float, nullable=False, default=0.00)
    period = db.Column(db.String(20), nullable=False, default="MONTHLY")  # "WEEKLY" or "MONTHLY"
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        limit = float(self.limit_amount)
        spent = float(self.spent_amount)
        remaining = max(0.0, limit - spent)

        return {
            "budget_id": self.id,
            "category": self.category,
            "limit_amount": round(limit, 2),
            "spent_amount": round(spent, 2),
            "remaining_amount": round(remaining, 2),
            "period": self.period,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None
        }
