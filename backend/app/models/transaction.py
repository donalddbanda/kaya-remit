from datetime import datetime, timezone
import uuid
from backend.app.extensions import db

def generate_transaction_id():
    return f"tx_{uuid.uuid4().hex[:9]}"

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.String(36), primary_key=True, default=generate_transaction_id)
    sender_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    recipient_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="MWK")
    category = db.Column(db.String(50), nullable=False, default="TRANSFER")
    status = db.Column(db.String(20), nullable=False, default="COMPLETED")
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_transactions")
    recipient = db.relationship("User", foreign_keys=[recipient_id], backref="received_transactions")

    def to_dict(self, current_user_id=None):
        formatted_date = self.timestamp.isoformat()
        if formatted_date.endswith("+00:00"):
            formatted_date = formatted_date[:-6] + "Z"
        elif not formatted_date.endswith("Z"):
            formatted_date += "Z"

        tx_type = "DEBIT"
        counterpart_name = "N/A"

        if current_user_id:
            if self.sender_id == current_user_id:
                tx_type = "DEBIT"
                counterpart_name = self.recipient.full_name if self.recipient else "External"
            else:
                tx_type = "CREDIT"
                counterpart_name = self.sender.full_name if self.sender else "External"
        else:
            if self.recipient:
                counterpart_name = self.recipient.full_name

        return {
            "transaction_id": self.id,
            "txn_id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "type": tx_type,
            "amount": round(float(self.amount), 2),
            "currency": self.currency,
            "category": self.category,
            "recipient_or_sender": counterpart_name,
            "status": self.status,
            "timestamp": formatted_date,
            "created_at": formatted_date
        }
