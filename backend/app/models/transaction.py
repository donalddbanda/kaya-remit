from datetime import datetime, timezone
import uuid
from backend.app.extensions import db

def generate_transaction_id():
    return f"tx_{uuid.uuid4().hex[:9]}"

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.String(36), primary_key=True, default=generate_transaction_id)
    wallet_id = db.Column(db.String(36), db.ForeignKey("wallets.id"), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(10), nullable=False)  # "DEBIT" or "CREDIT"
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="MWK")
    recipient_or_sender = db.Column(db.String(100), nullable=False)
    narration = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="COMPLETED")
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        formatted_date = self.created_at.isoformat()
        if formatted_date.endswith("+00:00"):
            formatted_date = formatted_date[:-6] + "Z"
        elif not formatted_date.endswith("Z"):
            formatted_date += "Z"

        return {
            "transaction_id": self.id,
            "type": self.type,
            "amount": round(float(self.amount), 2),
            "recipient_or_sender": self.recipient_or_sender,
            "status": self.status,
            "created_at": formatted_date
        }
