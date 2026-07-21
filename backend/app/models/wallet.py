from datetime import datetime, timezone
import uuid
from backend.app.extensions import db

def generate_wallet_id():
    return f"wal_{uuid.uuid4().hex[:9]}"

class Wallet(db.Model):
    __tablename__ = "wallets"

    id = db.Column(db.String(36), primary_key=True, default=generate_wallet_id)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    balance = db.Column(db.Float, nullable=False, default=0.00)
    currency = db.Column(db.String(10), nullable=False, default="MWK")
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "wallet_id": self.id,
            "currency": self.currency,
            "balance": round(float(self.balance), 2),
            "status": self.status
        }
