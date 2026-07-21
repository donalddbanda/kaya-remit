from marshmallow import Schema, fields, validate, validates, ValidationError

class TransferSchema(Schema):
    recipient_identifier = fields.String(required=True, validate=validate.Length(min=1, max=255))
    amount = fields.Float(required=True)
    currency = fields.String(load_default="MWK", validate=validate.Length(min=1, max=10))
    category = fields.String(load_default="TRANSFER", validate=validate.Length(min=1, max=50))
    narration = fields.String(load_default=None, validate=validate.Length(max=255))
    pin = fields.String(load_default=None)

    @validates("amount")
    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError("Amount must be a positive number.")

    @validates("recipient_identifier")
    def validate_recipient(self, value):
        if not value.strip():
            raise ValidationError("recipient_identifier cannot be empty.")
        return value.strip()
