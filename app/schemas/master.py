from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date, time
from decimal import Decimal


class MasterInvite(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    tier: str  # junior, middle, senior, expert
    branch_ids: List[UUID]
    service_ids: Optional[List[UUID]] = None
    specialization: Optional[str] = None


class MasterUpdate(BaseModel):
    tier: Optional[str] = None
    specialization: Optional[str] = None
    bio_ru: Optional[str] = None
    bio_kk: Optional[str] = None
    bio_en: Optional[str] = None
    experience_years: Optional[int] = None
    branch_ids: Optional[List[UUID]] = None
    service_ids: Optional[List[UUID]] = None
    permissions: Optional[Dict[str, Any]] = None


class MasterResponse(BaseModel):
    id: UUID
    tier: str
    specialization: Optional[str]
    bio_ru: Optional[str]
    experience_years: int
    rating: Decimal
    total_reviews: int
    is_active: bool
    user: Dict[str, Any]

    class Config:
        from_attributes = True


class ScheduleUpdate(BaseModel):
    branch_id: UUID
    regular_schedule: List[Dict[str, Any]]  # 7 days


class ScheduleExceptionCreate(BaseModel):
    exception_date: date
    exception_type: str  # day_off, custom_hours, fully_booked
    custom_start_time: Optional[time] = None
    custom_end_time: Optional[time] = None
    reason: Optional[str] = None


class ScheduleResponse(BaseModel):
    regular_schedule: List[Dict[str, Any]]
    exceptions: List[Dict[str, Any]]
