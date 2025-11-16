from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.schemas.auth import (
    GoogleAuthRequest,
    TokenResponse,
    PhoneAuthRequest,
    VerifyCodeRequest,
    RefreshTokenRequest
)
from app.models.user import User, UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    blacklist_token,
    sanitize_phone_number,
    validate_phone_format
)
from app.core.whatsapp import whatsapp_client
from app.core.redis_client import redis_client
from app.core.audit import log_authentication_attempt, log_security_event
from app.core.config import settings
from app.api.deps import get_current_user
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/request-code")
async def request_verification_code(
    request: Request,
    phone_request: PhoneAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Request phone verification code via WhatsApp

    Sends a 6-digit verification code to the provided phone number.
    Code expires in 5 minutes.
    Rate limited to prevent abuse.
    """
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"

    # Sanitize and validate phone number
    phone = sanitize_phone_number(phone_request.phone)
    if not validate_phone_format(phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format. Use E.164 format (e.g., +77012345678)"
        )

    # Check rate limiting for verification requests
    rate_limit_key = f"phone_verification:{phone}"
    attempts = redis_client.get_login_attempts(rate_limit_key)

    if attempts >= 3:
        log_security_event(
            event_type="phone_verification_rate_limit",
            severity="warning",
            description=f"Too many verification requests for phone {phone}",
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many verification requests. Please try again in {settings.ACCOUNT_LOCKOUT_DURATION_MINUTES} minutes."
        )

    # Send verification code via WhatsApp
    success, code, error = await whatsapp_client.send_verification_code(
        phone=phone,
        language=phone_request.language
    )

    if not success:
        log_security_event(
            event_type="whatsapp_send_failed",
            severity="warning",
            description=f"Failed to send WhatsApp code: {error}",
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error or "Failed to send verification code"
        )

    return {
        "success": True,
        "message": "Verification code sent successfully",
        "expires_in": settings.WHATSAPP_VERIFICATION_CODE_EXPIRE_MINUTES * 60,
        "phone": phone
    }


@router.post("/verify-code", response_model=TokenResponse)
async def verify_phone_code(
    request: Request,
    verify_request: VerifyCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Verify phone code and authenticate user

    Validates the verification code and creates or authenticates the user.
    Creates a new CLIENT user if phone number is new to the system.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # Sanitize phone number
    phone = sanitize_phone_number(verify_request.phone)

    # Get stored verification code from Redis
    stored_code = redis_client.get_verification_code(phone)

    if not stored_code:
        log_authentication_attempt(
            success=False,
            phone=phone,
            ip_address=client_ip,
            user_agent=user_agent,
            failure_reason="Code expired or not found"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired or not found. Please request a new code."
        )

    # Verify code matches
    if stored_code != verify_request.code:
        # Increment failed attempts
        attempts_key = f"code_attempts:{phone}"
        attempts = redis_client.increment_login_attempts(attempts_key)

        log_authentication_attempt(
            success=False,
            phone=phone,
            ip_address=client_ip,
            user_agent=user_agent,
            failure_reason="Invalid verification code"
        )

        if attempts >= 3:
            # Delete verification code after too many failed attempts
            redis_client.delete_verification_code(phone)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please request a new code."
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification code. {3 - attempts} attempts remaining."
        )

    # Code is valid - delete it and reset attempts
    redis_client.delete_verification_code(phone)
    redis_client.reset_login_attempts(f"code_attempts:{phone}")
    redis_client.reset_login_attempts(f"phone_verification:{phone}")

    # Find or create user
    user = db.query(User).filter(User.phone == phone).first()

    if not user:
        # Create new client user
        user = User(
            phone=phone,
            phone_verified=True,
            role=UserRole.CLIENT,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        log_authentication_attempt(
            success=True,
            user_id=str(user.id),
            phone=phone,
            ip_address=client_ip,
            user_agent=user_agent
        )
    else:
        # Update phone_verified status
        if not user.phone_verified:
            user.phone_verified = True
            db.commit()

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact support."
            )

        log_authentication_attempt(
            success=True,
            user_id=str(user.id),
            phone=phone,
            ip_address=client_ip,
            user_agent=user_agent
        )

    # Generate JWT tokens
    token_data = {
        "user_id": str(user.id),
        "role": user.role.value,
        "phone": user.phone,
    }
    access_token = create_access_token(token_data)
    refresh_token_str = create_refresh_token(token_data)

    # Create session in Redis
    session_data = {
        "user_id": str(user.id),
        "role": user.role.value,
        "ip_address": client_ip,
        "user_agent": user_agent
    }
    redis_client.create_session(
        user_id=str(user.id),
        session_data=session_data,
        ttl_seconds=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        user={
            "id": str(user.id),
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
        },
    )


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    request: Request,
    google_request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Google OAuth for salon staff

    OAuth authentication for salon owners, managers, and masters.
    Clients should use phone authentication instead.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    try:
        # Verify token with Google
        idinfo = id_token.verify_oauth2_token(
            google_request.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=30
        )

        # Extract user info
        google_id = idinfo['sub']
        email = idinfo.get('email')
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )

        # Find or create user
        user = db.query(User).filter(
            (User.email == email) | (User.google_id == google_id)
        ).first()

        if not user:
            # Create new salon owner user
            user = User(
                email=email,
                google_id=google_id,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.SALON_OWNER,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            log_authentication_attempt(
                success=True,
                user_id=str(user.id),
                email=email,
                ip_address=client_ip,
                user_agent=user_agent
            )
        else:
            # Update Google ID if missing
            if not user.google_id:
                user.google_id = google_id
                db.commit()

            # Check if user is active
            if not user.is_active:
                log_authentication_attempt(
                    success=False,
                    user_id=str(user.id),
                    email=email,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    failure_reason="Account inactive"
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is inactive. Contact support.",
                )

            # Restrict clients to phone auth
            if user.role == UserRole.CLIENT:
                log_authentication_attempt(
                    success=False,
                    user_id=str(user.id),
                    email=email,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    failure_reason="Client attempted OAuth login"
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Clients should use phone authentication",
                )

            log_authentication_attempt(
                success=True,
                user_id=str(user.id),
                email=email,
                ip_address=client_ip,
                user_agent=user_agent
            )

        # Generate JWT tokens
        token_data = {
            "user_id": str(user.id),
            "role": user.role.value,
            "email": user.email,
        }
        access_token = create_access_token(token_data)
        refresh_token_str = create_refresh_token(token_data)

        # Create session in Redis
        session_data = {
            "user_id": str(user.id),
            "role": user.role.value,
            "email": user.email,
            "ip_address": client_ip,
            "user_agent": user_agent
        }
        redis_client.create_session(
            user_id=str(user.id),
            session_data=session_data,
            ttl_seconds=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            user={
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
            },
        )

    except ValueError as e:
        log_authentication_attempt(
            success=False,
            ip_address=client_ip,
            user_agent=user_agent,
            failure_reason=f"Invalid Google token: {str(e)}"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}",
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token

    Implements token rotation for security.
    Old refresh token is blacklisted after use.
    """
    client_ip = request.client.host if request.client else "unknown"

    # Verify refresh token
    payload = verify_token(refresh_request.refresh_token, "refresh", check_blacklist=True)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Blacklist old refresh token (token rotation)
    blacklist_token(refresh_request.refresh_token)

    # Generate new tokens
    token_data = {
        "user_id": str(user.id),
        "role": user.role.value,
        "email": user.email,
        "phone": user.phone,
    }
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
        },
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user

    Blacklists current access token and deletes session from Redis.
    """
    # Get token from header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        # Blacklist access token
        blacklist_token(token)

    # Delete session from Redis
    redis_client.delete_session(str(current_user.id))

    return {"message": "Successfully logged out"}
