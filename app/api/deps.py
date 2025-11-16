from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List, Callable
from app.db.base import get_db
from app.core.security import verify_token
from app.models.user import User, UserRole
from app.models.salon import Salon, Master
from uuid import UUID
from app.core.audit import log_permission_denied, log_authentication_attempt

security = HTTPBearer()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user with enhanced security checks

    Validates JWT token, checks blacklist, and verifies user is active
    """
    token = credentials.credentials

    # Verify token with blacklist check
    payload = verify_token(token, "access", check_blacklist=True)

    if not payload:
        # Log failed authentication attempt
        client_ip = request.client.host if request.client else "unknown"
        log_authentication_attempt(
            success=False,
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
            failure_reason="Invalid or expired token"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.id == UUID(user_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Please contact support.",
        )

    # Check if user is soft-deleted
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted.",
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (redundant check, kept for backwards compatibility)"""
    return current_user


def require_role(allowed_roles: List[UserRole]):
    """
    Dependency to check user role with audit logging

    Usage:
        @router.get("/admin/data")
        async def admin_endpoint(user: User = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
            ...
    """

    def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            # Log permission denied
            client_ip = request.client.host if request.client else "unknown"
            log_permission_denied(
                user_id=str(current_user.id),
                action_type="access_endpoint",
                entity_type="api",
                required_permission=f"role:{','.join([r.value for r in allowed_roles])}",
                ip_address=client_ip
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join([r.value for r in allowed_roles])}",
            )
        return current_user

    return role_checker


def require_salon_owner(salon_id: UUID):
    """
    Dependency to verify user owns the salon

    Usage:
        @router.patch("/salons/{salon_id}")
        async def update_salon(
            salon_id: UUID,
            user: User = Depends(require_salon_owner(salon_id))
        ):
            ...
    """

    def owner_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Platform admins bypass ownership check
        if current_user.role == UserRole.PLATFORM_ADMIN:
            return current_user

        # Check salon ownership
        salon = db.query(Salon).filter(Salon.id == salon_id).first()

        if not salon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salon not found"
            )

        if salon.owner_id != current_user.id:
            # Log permission denied
            client_ip = request.client.host if request.client else "unknown"
            log_permission_denied(
                user_id=str(current_user.id),
                action_type="access_salon",
                entity_type="salon",
                entity_id=str(salon_id),
                required_permission="salon_owner",
                ip_address=client_ip
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this salon"
            )

        return current_user

    return owner_checker


def require_salon_staff(salon_id: UUID, include_masters: bool = True):
    """
    Dependency to verify user is salon staff (owner, manager, or optionally master)

    Args:
        salon_id: Salon UUID
        include_masters: Whether to allow masters (default: True)
    """

    def staff_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Platform admins bypass check
        if current_user.role == UserRole.PLATFORM_ADMIN:
            return current_user

        salon = db.query(Salon).filter(Salon.id == salon_id).first()

        if not salon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salon not found"
            )

        # Check if user is owner
        if salon.owner_id == current_user.id:
            return current_user

        # Check if user is manager
        if current_user.role == UserRole.SALON_MANAGER:
            # TODO: Add manager-salon relationship check when implemented
            return current_user

        # Check if user is master
        if include_masters and current_user.role == UserRole.MASTER:
            master = db.query(Master).filter(
                Master.user_id == current_user.id,
                Master.salon_id == salon_id,
                Master.is_active == True
            ).first()

            if master:
                return current_user

        # User is not authorized
        client_ip = request.client.host if request.client else "unknown"
        log_permission_denied(
            user_id=str(current_user.id),
            action_type="access_salon_staff",
            entity_type="salon",
            entity_id=str(salon_id),
            required_permission="salon_staff",
            ip_address=client_ip
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this salon"
        )

    return staff_checker


def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise
    Useful for public endpoints that have optional authentication

    Usage:
        @router.get("/public/salons")
        async def list_salons(user: Optional[User] = Depends(get_optional_current_user)):
            # Show different data based on whether user is authenticated
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token, "access", check_blacklist=True)

        if not payload:
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        user = db.query(User).filter(
            User.id == UUID(user_id),
            User.is_active == True,
            User.deleted_at.is_(None)
        ).first()

        return user

    except Exception:
        # Silently fail for optional authentication
        return None
