from marshmallow import Schema, fields, validate, validates, ValidationError

class UpdateProfileSchema(Schema):
    full_name = fields.String(load_default=None, validate=validate.Length(min=1, max=100))
    phone = fields.String(load_default=None, validate=validate.Length(min=8, max=30))

    @validates("full_name")
    def validate_full_name(self, value):
        if value is not None and not value.strip():
            raise ValidationError("Full name cannot be empty.")

    @validates("phone")
    def validate_phone(self, value):
        if value is not None and not value.strip().startswith("+"):
            raise ValidationError("Phone number must start with '+' followed by country code and local number.")

class SetPinSchema(Schema):
    pin = fields.String(required=True)

    @validates("pin")
    def validate_pin(self, value):
        stripped = str(value).strip()
        if not stripped.isdigit():
            raise ValidationError("PIN must contain only digits.")
        if not (4 <= len(stripped) <= 6):
            raise ValidationError("PIN must be between 4 and 6 digits long.")
        return stripped
