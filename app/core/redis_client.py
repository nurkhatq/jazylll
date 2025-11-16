"""
Redis client for session management, token blacklist, and rate limiting
"""
import redis
from typing import Optional
from app.core.config import settings
import json
from datetime import timedelta


class RedisClient:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            print("✅ Redis connected successfully")
        except redis.ConnectionError as e:
            print(f"⚠️  Redis connection failed: {e}")
            print("⚠️  Token blacklist and rate limiting will not work without Redis")
            self.redis_client = None

    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self.redis_client is not None

    # Token Blacklist Methods
    def blacklist_token(self, token: str, expires_in_seconds: int):
        """Add token to blacklist"""
        if not self.redis_client:
            return False

        key = f"{settings.REDIS_TOKEN_BLACKLIST_PREFIX}{token}"
        try:
            self.redis_client.setex(key, expires_in_seconds, "1")
            return True
        except Exception as e:
            print(f"Error blacklisting token: {e}")
            return False

    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        if not self.redis_client:
            return False  # Fail open if Redis unavailable

        key = f"{settings.REDIS_TOKEN_BLACKLIST_PREFIX}{token}"
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"Error checking token blacklist: {e}")
            return False

    # Session Management
    def create_session(self, user_id: str, session_data: dict, ttl_seconds: int):
        """Create user session"""
        if not self.redis_client:
            return None

        session_id = f"{settings.REDIS_SESSION_PREFIX}{user_id}"
        try:
            self.redis_client.setex(
                session_id,
                ttl_seconds,
                json.dumps(session_data)
            )
            return session_id
        except Exception as e:
            print(f"Error creating session: {e}")
            return None

    def get_session(self, user_id: str) -> Optional[dict]:
        """Get user session data"""
        if not self.redis_client:
            return None

        session_id = f"{settings.REDIS_SESSION_PREFIX}{user_id}"
        try:
            data = self.redis_client.get(session_id)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None

    def delete_session(self, user_id: str):
        """Delete user session (logout)"""
        if not self.redis_client:
            return False

        session_id = f"{settings.REDIS_SESSION_PREFIX}{user_id}"
        try:
            self.redis_client.delete(session_id)
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

    # Rate Limiting
    def check_rate_limit(self, identifier: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check rate limit for an identifier (IP, user_id, etc.)
        Returns (allowed: bool, remaining: int)
        """
        if not self.redis_client:
            return True, max_requests  # Fail open if Redis unavailable

        key = f"ratelimit:{identifier}"
        try:
            current = self.redis_client.get(key)

            if current is None:
                # First request in window
                self.redis_client.setex(key, window_seconds, "1")
                return True, max_requests - 1

            current_count = int(current)
            if current_count >= max_requests:
                return False, 0

            # Increment counter
            self.redis_client.incr(key)
            return True, max_requests - current_count - 1

        except Exception as e:
            print(f"Error checking rate limit: {e}")
            return True, max_requests  # Fail open on error

    def reset_rate_limit(self, identifier: str):
        """Reset rate limit for an identifier"""
        if not self.redis_client:
            return

        key = f"ratelimit:{identifier}"
        try:
            self.redis_client.delete(key)
        except Exception as e:
            print(f"Error resetting rate limit: {e}")

    # Login Attempts Tracking
    def increment_login_attempts(self, identifier: str) -> int:
        """Increment failed login attempts, returns current count"""
        if not self.redis_client:
            return 0

        key = f"login_attempts:{identifier}"
        try:
            count = self.redis_client.incr(key)
            if count == 1:
                # Set expiry on first attempt
                self.redis_client.expire(
                    key,
                    settings.ACCOUNT_LOCKOUT_DURATION_MINUTES * 60
                )
            return count
        except Exception as e:
            print(f"Error incrementing login attempts: {e}")
            return 0

    def get_login_attempts(self, identifier: str) -> int:
        """Get number of failed login attempts"""
        if not self.redis_client:
            return 0

        key = f"login_attempts:{identifier}"
        try:
            count = self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            print(f"Error getting login attempts: {e}")
            return 0

    def reset_login_attempts(self, identifier: str):
        """Reset login attempts after successful login"""
        if not self.redis_client:
            return

        key = f"login_attempts:{identifier}"
        try:
            self.redis_client.delete(key)
        except Exception as e:
            print(f"Error resetting login attempts: {e}")

    # Phone Verification Codes
    def store_verification_code(self, phone: str, code: str):
        """Store phone verification code"""
        if not self.redis_client:
            return False

        key = f"verification:{phone}"
        try:
            self.redis_client.setex(
                key,
                settings.WHATSAPP_VERIFICATION_CODE_EXPIRE_MINUTES * 60,
                code
            )
            return True
        except Exception as e:
            print(f"Error storing verification code: {e}")
            return False

    def get_verification_code(self, phone: str) -> Optional[str]:
        """Get stored verification code"""
        if not self.redis_client:
            return None

        key = f"verification:{phone}"
        try:
            return self.redis_client.get(key)
        except Exception as e:
            print(f"Error getting verification code: {e}")
            return None

    def delete_verification_code(self, phone: str):
        """Delete verification code after use"""
        if not self.redis_client:
            return

        key = f"verification:{phone}"
        try:
            self.redis_client.delete(key)
        except Exception as e:
            print(f"Error deleting verification code: {e}")

    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()


# Global Redis client instance
redis_client = RedisClient()
