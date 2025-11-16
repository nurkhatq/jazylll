"""
Security and Rate Limiting Middleware
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.redis_client import redis_client
from app.core.config import settings
from app.core.security import hash_ip_address
import time
from typing import Callable


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis
    Implements token bucket algorithm
    """

    async def dispatch(self, request: Request, call_next: Callable):
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"

        # Hash IP for privacy
        identifier = hash_ip_address(client_ip)

        # Check if this is an auth endpoint (stricter limits)
        is_auth_endpoint = request.url.path.startswith("/api/v1/auth")

        # Set rate limit based on endpoint
        if is_auth_endpoint:
            max_requests = settings.RATE_LIMIT_AUTH_PER_MINUTE
        else:
            max_requests = settings.RATE_LIMIT_PER_MINUTE

        # Check rate limit
        allowed, remaining = redis_client.check_rate_limit(
            identifier=f"{identifier}:{request.url.path}",
            max_requests=max_requests,
            window_seconds=60
        )

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline';"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Log sensitive operations for audit trail
    """

    # Sensitive endpoints to log
    AUDIT_PATHS = [
        "/api/v1/auth/",
        "/api/v1/users/",
        "/api/v1/salons/",
        "/api/v1/admin/",
    ]

    # Methods to audit
    AUDIT_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

    async def dispatch(self, request: Request, call_next: Callable):
        # Check if this request should be audited
        should_audit = (
            settings.ENABLE_AUDIT_LOGGING
            and request.method in self.AUDIT_METHODS
            and any(request.url.path.startswith(path) for path in self.AUDIT_PATHS)
        )

        if should_audit:
            # Capture request details
            start_time = time.time()
            user_agent = request.headers.get("user-agent", "")
            client_ip = request.client.host if request.client else "unknown"

            # Get user ID from auth header if available
            user_id = None
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                from app.core.security import verify_token
                token = auth_header.split(" ")[1]
                payload = verify_token(token, check_blacklist=False)
                if payload:
                    user_id = payload.get("user_id")

            # Process request
            response = await call_next(request)

            # Log after response (async operation)
            duration = time.time() - start_time

            # Import here to avoid circular dependency
            from app.core.audit import log_audit_event

            # Create audit log entry
            await log_audit_event(
                user_id=user_id,
                action_type=f"{request.method}_{request.url.path}",
                entity_type=self._extract_entity_type(request.url.path),
                ip_address=client_ip,
                user_agent=user_agent,
                status_code=response.status_code,
                duration_ms=int(duration * 1000)
            )

            return response
        else:
            return await call_next(request)

    def _extract_entity_type(self, path: str) -> str:
        """Extract entity type from path"""
        if "/salons/" in path:
            return "salon"
        elif "/users/" in path:
            return "user"
        elif "/auth/" in path:
            return "auth"
        elif "/bookings/" in path:
            return "booking"
        elif "/masters/" in path:
            return "master"
        elif "/services/" in path:
            return "service"
        elif "/admin/" in path:
            return "admin"
        return "unknown"


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate incoming requests for common attack patterns
    """

    # Suspicious patterns in request data
    SUSPICIOUS_PATTERNS = [
        "<script",
        "javascript:",
        "onerror=",
        "onload=",
        "../",
        "DROP TABLE",
        "SELECT * FROM",
        "UNION SELECT",
        "INSERT INTO",
    ]

    async def dispatch(self, request: Request, call_next: Callable):
        # Check URL for suspicious patterns
        url_str = str(request.url).lower()
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern.lower() in url_str:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request format"}
                )

        # Check headers
        user_agent = request.headers.get("user-agent", "")
        if len(user_agent) > 500 or not user_agent:
            # Block requests with suspicious user agents
            if settings.ENVIRONMENT == "production":
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request"}
                )

        return await call_next(request)
