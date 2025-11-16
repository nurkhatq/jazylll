from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import secrets
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add issued at timestamp and unique JTI (JWT ID)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": secrets.token_urlsafe(16)  # Unique token ID for blacklisting
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Add issued at timestamp and unique JTI
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16)
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access", check_blacklist: bool = True) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token

    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')
        check_blacklist: Whether to check Redis blacklist

    Returns:
        Token payload dict or None if invalid
    """
    try:
        # Decode and verify token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Check token type
        if payload.get("type") != token_type:
            return None

        # Check if token is blacklisted (if Redis is available)
        if check_blacklist:
            from app.core.redis_client import redis_client
            jti = payload.get("jti")
            if jti and redis_client.is_token_blacklisted(jti):
                return None

        return payload

    except JWTError as e:
        # Log JWT errors for security monitoring
        print(f"JWT verification failed: {e}")
        return None


def blacklist_token(token: str) -> bool:
    """
    Add token to blacklist

    Args:
        token: JWT token to blacklist

    Returns:
        True if successful, False otherwise
    """
    try:
        from app.core.redis_client import redis_client

        # Decode without verification to get JTI and expiry
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}  # Don't verify expiry when blacklisting
        )

        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti or not exp:
            return False

        # Calculate remaining TTL
        expires_at = datetime.fromtimestamp(exp)
        ttl_seconds = int((expires_at - datetime.utcnow()).total_seconds())

        if ttl_seconds > 0:
            return redis_client.blacklist_token(jti, ttl_seconds)

        return True  # Already expired, no need to blacklist

    except Exception as e:
        print(f"Error blacklisting token: {e}")
        return False


def generate_verification_code() -> str:
    """Generate 6-digit verification code"""
    code_length = settings.WHATSAPP_VERIFICATION_CODE_LENGTH
    max_value = (10 ** code_length) - 1
    return str(secrets.randbelow(max_value)).zfill(code_length)


def generate_invitation_token() -> str:
    """Generate unique invitation token for master invitations"""
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_session_token() -> str:
    """Generate secure session token"""
    return secrets.token_urlsafe(32)


def hash_ip_address(ip: str) -> str:
    """Hash IP address for privacy-preserving rate limiting"""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def validate_phone_format(phone: str) -> bool:
    """
    Validate phone number format (E.164)
    Format: +[country code][number]
    Example: +77012345678
    """
    import re
    pattern = r'^\+\d{10,15}$'
    return bool(re.match(pattern, phone))


def sanitize_phone_number(phone: str) -> str:
    """
    Sanitize phone number to E.164 format
    Removes spaces, dashes, parentheses
    """
    import re
    # Remove all non-digit characters except leading +
    cleaned = re.sub(r'[^\d+]', '', phone)

    # Ensure it starts with +
    if not cleaned.startswith('+'):
        # Assume Kazakhstan if no country code
        cleaned = '+7' + cleaned.lstrip('87')

    return cleaned
