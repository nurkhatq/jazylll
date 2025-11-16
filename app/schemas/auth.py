from pydantic import BaseModel, Field, field_validator
from typing import Optional


class PhoneAuthRequest(BaseModel):
    """Request for phone authentication code"""
    phone: str = Field(..., description="Phone number in E.164 format (+77012345678)")
    language: Optional[str] = Field("ru", description="Language for message (ru, kk, en)")


class VerifyCodeRequest(BaseModel):
    """Request to verify phone code"""
    phone: str = Field(..., description="Phone number in E.164 format")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class GoogleAuthRequest(BaseModel):
    """Request for Google OAuth authentication"""
    id_token: str = Field(..., description="Google ID token from OAuth flow")


class TokenResponse(BaseModel):
    """Authentication response with JWT tokens"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    user: dict = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str = Field(..., description="Refresh token")


# Legacy schemas (keep for backwards compatibility)
PhoneRequest = PhoneAuthRequest
CodeVerificationRequest = VerifyCodeRequest


class CodeSentResponse(BaseModel):
    """Response after sending verification code"""
    code_sent: bool
    expires_in: int
