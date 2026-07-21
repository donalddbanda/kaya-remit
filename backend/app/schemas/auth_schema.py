from marshmallow import Schema, fields, validate, validates, ValidationError
import re

class RegisterSchema(Schema):
    full_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    phone = fields.String(required=True, validate=validate.Length(min=8, max=30))
    password = fields.String(required=True, validate=validate.Length(min=6, max=128))

    @validates("full_name")
    def validate_full_name(self, value):
        if not value.strip():
            raise ValidationError("Full name cannot be empty.")
        return value.strip()

    @validates("phone")
    def validate_phone(self, value):
        if not value.strip().startswith("+"):
            raise ValidationError("Phone number must start with '+' followed by country code and local number.")
        return value.strip()

    @validates("email")
    def validate_email_strip(self, value):
        return value.strip().lower()

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1))
