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


class SalonCategory(Base):
    __tablename__ = "salon_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False, index=True)
    name_ru = Column(String, nullable=False)
    name_kk = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    description_ru = Column(Text, nullable=True)
    description_kk = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    icon_url = Column(String, nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_code = Column(String, unique=True, nullable=False)
    plan_name_ru = Column(String, nullable=False)
    plan_name_kk = Column(String, nullable=False)
    plan_name_en = Column(String, nullable=False)
    description_ru = Column(Text, nullable=True)
    description_kk = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    monthly_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="KZT")
    features = Column(JSON, nullable=False)  # max_masters, max_branches, etc.
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Salon(Base):
    __tablename__ = "salons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("salon_categories.id", ondelete="RESTRICT"), nullable=False
    )
    subscription_plan_id = Column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=True
    )

    business_name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)

    description_ru = Column(Text, nullable=True)
    description_kk = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)

    logo_url = Column(String, nullable=True)
    cover_image_url = Column(String, nullable=True)

    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    social_links = Column(JSON, nullable=True)  # {instagram, facebook, whatsapp}

    subscription_start_date = Column(Date, nullable=True)
    subscription_end_date = Column(Date, nullable=True)

    is_active = Column(Boolean, default=True)
    is_visible_in_catalog = Column(Boolean, default=True)

    advertising_budget = Column(Numeric(10, 2), default=0)
    auction_bid = Column(Numeric(10, 2), default=0)

    rating = Column(Numeric(3, 2), default=0)
    total_reviews = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owner = relationship("User", backref="owned_salons", foreign_keys=[owner_id])
    category = relationship("SalonCategory", backref="salons")
    subscription_plan = relationship("SubscriptionPlan", backref="salons")


class SalonBranch(Base):
    __tablename__ = "salon_branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    salon_id = Column(UUID(as_uuid=True), ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    branch_name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)

    country = Column(String, default="Kazakhstan")
    city = Column(String, nullable=False)
    street_address = Column(String, nullable=False)
    building_number = Column(String, nullable=False)
    postal_code = Column(String, nullable=True)

    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)

    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)

    working_hours = Column(JSON, nullable=True)  # {monday: {is_working, open_time, close_time, breaks}}

    is_main = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    salon = relationship("Salon", backref="branches")


class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    salon_id = Column(UUID(as_uuid=True), ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    service_name_ru = Column(String, nullable=False)
    service_name_kk = Column(String, nullable=True)
    service_name_en = Column(String, nullable=True)

    description_ru = Column(Text, nullable=True)
    description_kk = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)

    duration_minutes = Column(Integer, nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    price_tiers = Column(JSON, nullable=True)  # [{master_tier, price}]

    category = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    salon = relationship("Salon", backref="services")


class MasterTier(str, enum.Enum):
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"
    EXPERT = "expert"


class Master(Base):
    __tablename__ = "masters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    salon_id = Column(UUID(as_uuid=True), ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    tier = Column(SQLEnum(MasterTier), default=MasterTier.MIDDLE)

    bio_ru = Column(Text, nullable=True)
    bio_kk = Column(Text, nullable=True)
    bio_en = Column(Text, nullable=True)

    specialization = Column(Text, nullable=True)
    portfolio_images = Column(JSON, nullable=True)  # Array of URLs
    experience_years = Column(Integer, default=0)

    rating = Column(Numeric(3, 2), default=0)
    total_reviews = Column(Integer, default=0)

    permissions = Column(JSON, nullable=True)  # {can_manage_own_schedule, can_edit_profile, etc}

    is_active = Column(Boolean, default=True)
    invited_at = Column(DateTime(timezone=True), nullable=True)
    joined_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="master_profiles")
    salon = relationship("Salon", backref="masters")


class MasterBranch(Base):
    __tablename__ = "master_branches"

    master_id = Column(
        UUID(as_uuid=True), ForeignKey("masters.id", ondelete="CASCADE"), primary_key=True
    )
    branch_id = Column(
        UUID(as_uuid=True), ForeignKey("salon_branches.id", ondelete="CASCADE"), primary_key=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    master = relationship("Master", backref="master_branches")
    branch = relationship("SalonBranch", backref="branch_masters")


class MasterService(Base):
    __tablename__ = "master_services"

    master_id = Column(
        UUID(as_uuid=True), ForeignKey("masters.id", ondelete="CASCADE"), primary_key=True
    )
    service_id = Column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), primary_key=True
    )

    custom_price = Column(Numeric(10, 2), nullable=True)
    custom_description_ru = Column(Text, nullable=True)
    custom_description_kk = Column(Text, nullable=True)
    custom_description_en = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    master = relationship("Master", backref="master_services")
    service = relationship("Service", backref="service_masters")


class MasterSchedule(Base):
    __tablename__ = "master_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    master_id = Column(UUID(as_uuid=True), ForeignKey("masters.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(
        UUID(as_uuid=True), ForeignKey("salon_branches.id", ondelete="CASCADE"), nullable=False
    )

    day_of_week = Column(Integer, nullable=False)  # 1-7 (Monday-Sunday)
    is_working = Column(Boolean, default=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    breaks = Column(JSON, nullable=True)  # [{break_start, break_end, reason}]

    __table_args__ = (UniqueConstraint("master_id", "branch_id", "day_of_week"),)

    # Relationships
    master = relationship("Master", backref="schedules")
    branch = relationship("SalonBranch", backref="master_schedules")


class ExceptionType(str, enum.Enum):
    DAY_OFF = "day_off"
    CUSTOM_HOURS = "custom_hours"
    FULLY_BOOKED = "fully_booked"


class ScheduleException(Base):
    __tablename__ = "schedule_exceptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    master_id = Column(UUID(as_uuid=True), ForeignKey("masters.id", ondelete="CASCADE"), nullable=False)

    exception_date = Column(Date, nullable=False)
    exception_type = Column(SQLEnum(ExceptionType), nullable=False)

    custom_start_time = Column(Time, nullable=True)
    custom_end_time = Column(Time, nullable=True)
    reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    master = relationship("Master", backref="schedule_exceptions")


class SiteCustomization(Base):
    __tablename__ = "site_customizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    salon_id = Column(
        UUID(as_uuid=True), ForeignKey("salons.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    template_name = Column(String, default="modern")  # modern, classic, minimalist, luxury
    color_scheme = Column(JSON, nullable=True)  # {primary_color, secondary_color, ...}
    fonts = Column(JSON, nullable=True)  # {heading_font, body_font}
    hero_section = Column(JSON, nullable=True)  # {title, subtitle, background_image_url, ...}
    sections = Column(JSON, nullable=True)  # [{section_type, is_visible, sort_order}]

    custom_text_ru = Column(Text, nullable=True)
    custom_text_kk = Column(Text, nullable=True)
    custom_text_en = Column(Text, nullable=True)

    favicon_url = Column(String, nullable=True)
    seo_settings = Column(JSON, nullable=True)  # {meta_title, meta_description, meta_keywords}

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    salon = relationship("Salon", backref="site_customization", uselist=False)
