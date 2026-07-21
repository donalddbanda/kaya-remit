from marshmallow import Schema, fields, validate, validates, ValidationError

class CreateBudgetSchema(Schema):
    category = fields.String(required=True, validate=validate.Length(min=1, max=100))
    limit_amount = fields.Float(required=True)
    period = fields.String(load_default="MONTHLY", validate=validate.OneOf(["WEEKLY", "MONTHLY"]))
    start_date = fields.String(load_default=None)
    end_date = fields.String(load_default=None)

    @validates("limit_amount")
    def validate_limit_amount(self, value):
        if value <= 0:
            raise ValidationError("limit_amount must be a positive number.")

    @validates("category")
    def validate_category(self, value):
        if not value.strip():
            raise ValidationError("category cannot be empty.")
        return value.strip()
