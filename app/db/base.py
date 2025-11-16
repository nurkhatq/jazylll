from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Import all models here to ensure they are registered with Base metadata
# This is required for Alembic to detect all models and generate migrations
from app.models.user import User
from app.models.salon import (
    SalonCategory,
    Salon,
    SalonBranch,
    Service,
    Master,
    MasterBranch,
    MasterService,
    MasterSchedule,
    ScheduleException,
    SiteCustomization,
    SubscriptionPlan,
)
from app.models.booking import Booking, Review
from app.models.payment import Payment
from app.models.catalog import CatalogImpression, CatalogClick
from app.models.communication import (
    WhatsAppSession,
    WhatsAppMessage,
    VerificationCode,
    Notification,
)
from app.models.audit import AuditLog


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
