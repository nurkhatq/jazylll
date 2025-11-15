from sqlalchemy import Column, Integer, Boolean, DateTime, Date, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


class CatalogImpression(Base):
    __tablename__ = "catalog_impressions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    salon_id = Column(UUID(as_uuid=True), ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    impression_date = Column(Date, nullable=False, index=True)
    impression_hour = Column(Integer, nullable=False)  # 0-23
    position = Column(Integer, nullable=False)

    is_promoted = Column(Boolean, default=False)
    cost = Column(Numeric(10, 2), default=0)

    # Relationships
    salon = relationship("Salon", backref="catalog_impressions")


class CatalogClick(Base):
    __tablename__ = "catalog_clicks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    salon_id = Column(UUID(as_uuid=True), ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    is_promoted = Column(Boolean, default=False)
    cost = Column(Numeric(10, 2), default=0)

    session_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    salon = relationship("Salon", backref="catalog_clicks")
    client = relationship("User", backref="catalog_clicks", foreign_keys=[client_id])
