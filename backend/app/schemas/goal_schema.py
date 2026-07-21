from marshmallow import Schema, fields, validate, validates, ValidationError

class CreateGoalSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=150))
    target_amount = fields.Float(required=True)
    target_date = fields.String(load_default=None)

    @validates("target_amount")
    def validate_target_amount(self, value):
        if value <= 0:
            raise ValidationError("target_amount must be a positive number.")

    @validates("title")
    def validate_title(self, value):
        if not value.strip():
            raise ValidationError("title cannot be empty.")
        return value.strip()

class DepositGoalSchema(Schema):
    amount = fields.Float(required=True)

    @validates("amount")
    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError("amount must be a positive number.")
