from sqlalchemy import Column, String, Boolean, Integer, Enum as SQLEnum, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.base import Base


class WhatsAppSessionStatus(str, enum.Enum):
    INITIALIZING = "initializing"
    QR_READY = "qr_ready"
    AUTHENTICATED = "authenticated"
    DISCONNECTED = "disconnected"
    FAILED = "failed"


class WhatsAppSession(Base):
    __tablename__ = "whatsapp_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, unique=True, nullable=False)
    qr_code = Column(Text, nullable=True)
    status = Column(SQLEnum(WhatsAppSessionStatus), default=WhatsAppSessionStatus.INITIALIZING)

    authenticated_at = Column(DateTime(timezone=True), nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    connection_attempts = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WhatsAppMessageType(str, enum.Enum):
    VERIFICATION_CODE = "verification_code"
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_REMINDER = "booking_reminder"
    BOOKING_CANCELLATION = "booking_cancellation"
    REVIEW_REQUEST = "review_request"


class WhatsAppMessageStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    phone_number = Column(String, nullable=False, index=True)

    message_type = Column(SQLEnum(WhatsAppMessageType), nullable=False)
    message_body = Column(Text, nullable=False)
    status = Column(SQLEnum(WhatsAppMessageStatus), default=WhatsAppMessageStatus.QUEUED, index=True)

    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="whatsapp_messages", foreign_keys=[user_id])


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    attempts = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NotificationType(str, enum.Enum):
    BOOKING_CREATED = "booking_created"
    BOOKING_REMINDER = "booking_reminder"
    BOOKING_CANCELLED = "booking_cancelled"
    REVIEW_RECEIVED = "review_received"
    PAYMENT_SUCCESSFUL = "payment_successful"
    SUBSCRIPTION_EXPIRING = "subscription_expiring"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    data = Column(UUID, nullable=True)  # Additional data for navigation

    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    sent_via = Column(ARRAY(String), nullable=True)  # [whatsapp, email, push, in_app]

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="notifications", foreign_keys=[user_id])
