from sqlalchemy import Column, String, Enum as SQLEnum, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.base import Base


class PaymentType(str, enum.Enum):
    SUBSCRIPTION = "subscription"
    ADVERTISING_BUDGET = "advertising_budget"


class PaymentMethod(str, enum.Enum):
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    ELECTRONIC_WALLET = "electronic_wallet"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    salon_id = Column(UUID(as_uuid=True), ForeignKey("salons.id", ondelete="RESTRICT"), nullable=False)

    payment_type = Column(SQLEnum(PaymentType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="KZT")

    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)

    transaction_id = Column(String, unique=True, nullable=True, index=True)
    payment_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    salon = relationship("Salon", backref="payments")
