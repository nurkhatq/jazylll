from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.base import Base


class UserRole(str, enum.Enum):
    PLATFORM_ADMIN = "platform_admin"
    SALON_OWNER = "salon_owner"
    SALON_MANAGER = "salon_manager"
    MASTER = "master"
    CLIENT = "client"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    phone_verified = Column(Boolean, default=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    middle_name = Column(String, nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CLIENT)
    google_id = Column(String, unique=True, nullable=True, index=True)
    photo_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
