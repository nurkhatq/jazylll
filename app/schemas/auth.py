from pydantic import BaseModel, Field, field_validator
from typing import Optional
import phonenumbers


class PhoneRequest(BaseModel):
    phone: str = Field(..., description="Phone number in E.164 format (+77012345678)")
    language: Optional[str] = Field("ru", description="Language for message (ru, kk, en)")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        try:
            parsed = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format. Use E.164 format (+77012345678)")


class CodeVerificationRequest(BaseModel):
    phone: str
    code: str = Field(..., min_length=6, max_length=6)


class GoogleAuthRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CodeSentResponse(BaseModel):
    code_sent: bool
    expires_in: int
