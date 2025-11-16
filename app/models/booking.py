from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    Enum as SQLEnum,
    DateTime,
    Text,
    ForeignKey,
    Numeric,
    Date,
    Time,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.base import Base


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED_BY_CLIENT = "cancelled_by_client"
    CANCELLED_BY_SALON = "cancelled_by_salon"
    NO_SHOW = "no_show"


class BookingCreatedVia(str, enum.Enum):
    WEBSITE = "website"
    MOBILE_APP = "mobile_app"
    CATALOG = "catalog"
    MANAGER = "manager"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    master_id = Column(UUID(as_uuid=True), ForeignKey("masters.id", ondelete="RESTRICT"), nullable=False)
    service_id = Column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id = Column(
        UUID(as_uuid=True), ForeignKey("salon_branches.id", ondelete="RESTRICT"), nullable=False
    )

    booking_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    final_price = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, index=True)
    created_via = Column(SQLEnum(BookingCreatedVia), nullable=True)

    notes_from_client = Column(Text, nullable=True)
    notes_for_master = Column(Text, nullable=True)

    reminded_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("User", backref="bookings", foreign_keys=[client_id])
    master = relationship("Master", backref="bookings")
    service = relationship("Service", backref="bookings")
    branch = relationship("SalonBranch", backref="bookings")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    salon_id = Column(UUID(as_uuid=True), ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    master_id = Column(UUID(as_uuid=True), ForeignKey("masters.id", ondelete="CASCADE"), nullable=True)

    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=True)
    review_photos = Column(JSON, nullable=True)  # Array of photo URLs

    is_verified = Column(Boolean, default=True)
    is_visible = Column(Boolean, default=True, index=True)
    moderation_flags = Column(JSON, nullable=True)  # Auto-moderation flags: {spam: bool, inappropriate_language: bool, suspicious: bool}

    salon_response = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="rating_check"),)

    # Relationships
    booking = relationship("Booking", backref="review", uselist=False)
    client = relationship("User", backref="reviews", foreign_keys=[client_id])
    salon = relationship("Salon", backref="reviews")
    master = relationship("Master", backref="reviews")
