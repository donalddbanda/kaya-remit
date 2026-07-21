from datetime import datetime, timezone
import uuid
from backend.app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

def generate_user_id():
    return f"usr_{uuid.uuid4().hex[:9]}"

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=generate_user_id)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    transaction_pin_hash = db.Column(db.String(255), nullable=True)
    kyc_status = db.Column(db.String(20), nullable=False, default="VERIFIED")
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    wallet = db.relationship("Wallet", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def has_pin(self):
        return self.transaction_pin_hash is not None

    def set_pin(self, pin):
        """Hash and store a transaction PIN. PIN is never logged or stored as plaintext."""
        self.transaction_pin_hash = generate_password_hash(str(pin))

    def check_pin(self, pin):
        """Verify a transaction PIN against the stored hash."""
        if not self.transaction_pin_hash:
            return False
        return check_password_hash(self.transaction_pin_hash, str(pin))

    def to_dict(self):
        # Format created_at to end with 'Z' if it is UTC
        formatted_date = self.created_at.isoformat()
        if formatted_date.endswith("+00:00"):
            formatted_date = formatted_date[:-6] + "Z"
        elif not formatted_date.endswith("Z"):
            formatted_date += "Z"
        return {
            "user_id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "kyc_status": self.kyc_status,
            "has_pin": self.has_pin,
            "created_at": formatted_date
        }
