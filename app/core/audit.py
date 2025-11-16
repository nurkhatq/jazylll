"""
Comprehensive Audit Logging System

Logs all security-sensitive operations for compliance and security monitoring
"""
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.db.base import get_db
from typing import Optional, Dict, Any
from uuid import UUID
import json
from datetime import datetime


async def log_audit_event(
    user_id: Optional[str],
    action_type: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status_code: Optional[int] = None,
    duration_ms: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Create an audit log entry

    Args:
        user_id: ID of user performing action (None for anonymous)
        action_type: Type of action (e.g., 'user_login', 'salon_created')
        entity_type: Type of entity affected (e.g., 'user', 'salon', 'booking')
        entity_id: ID of affected entity
        changes: Dict of changes made (old_values, new_values)
        ip_address: Client IP address
        user_agent: Client user agent string
        status_code: HTTP status code of response
        duration_ms: Request duration in milliseconds
        metadata: Additional metadata
    """
    try:
        # Get database session (note: this is a simplified version)
        # In production, you'd want to use background tasks for async logging
        from app.db.base import SessionLocal

        db = SessionLocal()

        audit_entry = AuditLog(
            user_id=UUID(user_id) if user_id else None,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=UUID(entity_id) if entity_id else None,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,  # Truncate long user agents
            metadata=metadata or {}
        )

        # Add additional metadata
        if status_code:
            audit_entry.metadata["status_code"] = status_code
        if duration_ms:
            audit_entry.metadata["duration_ms"] = duration_ms

        db.add(audit_entry)
        db.commit()
        db.close()

    except Exception as e:
        print(f"❌ Error logging audit event: {e}")
        # Don't fail the request if audit logging fails
        pass


def log_authentication_attempt(
    success: bool,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    failure_reason: Optional[str] = None
):
    """Log authentication attempts (login, verification, etc.)"""
    from app.db.base import SessionLocal

    try:
        db = SessionLocal()

        metadata = {
            "success": success,
            "email": email,
            "phone": phone,
            "failure_reason": failure_reason
        }

        audit_entry = AuditLog(
            user_id=UUID(user_id) if user_id else None,
            action_type="authentication_attempt",
            entity_type="auth",
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            metadata=metadata
        )

        db.add(audit_entry)
        db.commit()
        db.close()

    except Exception as e:
        print(f"❌ Error logging authentication attempt: {e}")


def log_permission_denied(
    user_id: str,
    action_type: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    required_permission: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Log permission denied events for security monitoring"""
    from app.db.base import SessionLocal

    try:
        db = SessionLocal()

        metadata = {
            "denied": True,
            "required_permission": required_permission,
            "severity": "warning"
        }

        audit_entry = AuditLog(
            user_id=UUID(user_id),
            action_type=f"permission_denied_{action_type}",
            entity_type=entity_type,
            entity_id=UUID(entity_id) if entity_id else None,
            ip_address=ip_address,
            metadata=metadata
        )

        db.add(audit_entry)
        db.commit()
        db.close()

    except Exception as e:
        print(f"❌ Error logging permission denied: {e}")


def log_data_access(
    user_id: str,
    entity_type: str,
    entity_id: str,
    access_type: str = "read",  # read, export, download
    ip_address: Optional[str] = None
):
    """Log sensitive data access for GDPR compliance"""
    from app.db.base import SessionLocal

    try:
        db = SessionLocal()

        metadata = {
            "access_type": access_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        audit_entry = AuditLog(
            user_id=UUID(user_id),
            action_type=f"data_access_{access_type}",
            entity_type=entity_type,
            entity_id=UUID(entity_id),
            ip_address=ip_address,
            metadata=metadata
        )

        db.add(audit_entry)
        db.commit()
        db.close()

    except Exception as e:
        print(f"❌ Error logging data access: {e}")


def log_security_event(
    event_type: str,
    severity: str,  # info, warning, critical
    description: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Log security events (rate limit exceeded, suspicious activity, etc.)"""
    from app.db.base import SessionLocal

    try:
        db = SessionLocal()

        event_metadata = metadata or {}
        event_metadata.update({
            "severity": severity,
            "description": description,
            "timestamp": datetime.utcnow().isoformat()
        })

        audit_entry = AuditLog(
            user_id=UUID(user_id) if user_id else None,
            action_type=f"security_event_{event_type}",
            entity_type="security",
            ip_address=ip_address,
            metadata=event_metadata
        )

        db.add(audit_entry)
        db.commit()
        db.close()

        # Print critical events to console for immediate attention
        if severity == "critical":
            print(f"🚨 CRITICAL SECURITY EVENT: {event_type} - {description}")

    except Exception as e:
        print(f"❌ Error logging security event: {e}")


class AuditContext:
    """
    Context manager for auditing operations with before/after state

    Usage:
        async with AuditContext(user_id, "update_salon", "salon", salon_id) as audit:
            audit.set_old_values({"name": "Old Name"})
            # ... perform update ...
            audit.set_new_values({"name": "New Name"})
    """

    def __init__(
        self,
        user_id: str,
        action_type: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        self.user_id = user_id
        self.action_type = action_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.old_values = {}
        self.new_values = {}
        self.start_time = None

    def set_old_values(self, values: Dict[str, Any]):
        """Set old values before change"""
        self.old_values = values

    def set_new_values(self, values: Dict[str, Any]):
        """Set new values after change"""
        self.new_values = values

    async def __aenter__(self):
        self.start_time = datetime.utcnow()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = int((datetime.utcnow() - self.start_time).total_seconds() * 1000)

        # Log the audit event
        await log_audit_event(
            user_id=self.user_id,
            action_type=self.action_type,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            changes={
                "old_values": self.old_values,
                "new_values": self.new_values
            } if self.old_values or self.new_values else None,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            duration_ms=duration_ms,
            metadata={
                "success": exc_type is None,
                "error": str(exc_val) if exc_val else None
            }
        )
