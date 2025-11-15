from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db.base import get_db
from app.schemas.auth import (
    PhoneRequest,
    CodeVerificationRequest,
    GoogleAuthRequest,
    TokenResponse,
    RefreshTokenRequest,
    CodeSentResponse,
)
from app.models.user import User, UserRole
from app.models.communication import VerificationCode, WhatsAppMessage, WhatsAppMessageType
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_verification_code,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/request-code", response_model=CodeSentResponse)
async def request_verification_code(request: PhoneRequest, db: Session = Depends(get_db)):
    """Request verification code via WhatsApp"""
    # Check for rate limiting (1 minute between requests)
    recent_code = (
        db.query(VerificationCode)
        .filter(
            VerificationCode.phone_number == request.phone,
            VerificationCode.created_at > datetime.utcnow() - timedelta(seconds=60),
        )
        .first()
    )

    if recent_code:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting a new code",
        )

    # Generate verification code
    code = generate_verification_code()
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    # Save code to database
    verification_code = VerificationCode(
        phone_number=request.phone, code=code, expires_at=expires_at
    )
    db.add(verification_code)

    # Queue WhatsApp message
    message = WhatsAppMessage(
        phone_number=request.phone,
        message_type=WhatsAppMessageType.VERIFICATION_CODE,
        message_body=f"Your Jazyl verification code is: {code}. Valid for 5 minutes.",
    )
    db.add(message)

    db.commit()

    return CodeSentResponse(code_sent=True, expires_in=300)


@router.post("/verify-code", response_model=TokenResponse)
async def verify_code(request: CodeVerificationRequest, db: Session = Depends(get_db)):
    """Verify code and authenticate user"""
    # Find valid verification code
    verification = (
        db.query(VerificationCode)
        .filter(
            VerificationCode.phone_number == request.phone,
            VerificationCode.code == request.code,
            VerificationCode.is_used == False,
            VerificationCode.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if not verification:
        # Increment attempts
        all_codes = (
            db.query(VerificationCode)
            .filter(
                VerificationCode.phone_number == request.phone,
                VerificationCode.expires_at > datetime.utcnow(),
            )
            .all()
        )

        for code_record in all_codes:
            code_record.attempts += 1
            if code_record.attempts >= 3:
                code_record.is_used = True

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code",
        )

    # Mark code as used
    verification.is_used = True
    verification.verified_at = datetime.utcnow()

    # Find or create user
    user = db.query(User).filter(User.phone == request.phone).first()
    if not user:
        user = User(phone=request.phone, phone_verified=True, role=UserRole.CLIENT, is_active=True)
        db.add(user)
    else:
        user.phone_verified = True

    db.commit()
    db.refresh(user)

    # Generate tokens
    token_data = {"user_id": str(user.id), "role": user.role.value, "phone": user.phone}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
        },
    )


@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate with Google OAuth"""
    # TODO: Implement Google token verification
    # For now, return error indicating implementation needed
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth implementation requires Google client credentials configuration",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token"""
    payload = verify_token(request.refresh_token, "refresh")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Generate new tokens
    token_data = {"user_id": str(user.id), "role": user.role.value, "phone": user.phone}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user={
            "id": str(user.id),
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
        },
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """Logout user (client should discard tokens)"""
    # TODO: Implement token blacklisting with Redis
    return None
