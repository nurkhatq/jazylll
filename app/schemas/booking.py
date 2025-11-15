from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date, time, datetime
from decimal import Decimal


class BookingCreate(BaseModel):
    master_id: UUID
    service_id: UUID
    branch_id: UUID
    booking_date: date
    start_time: time
    notes_from_client: Optional[str] = None


class BookingResponse(BaseModel):
    id: UUID
    client_id: UUID
    master_id: UUID
    service_id: UUID
    branch_id: UUID
    booking_date: date
    start_time: time
    end_time: time
    final_price: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AvailableSlot(BaseModel):
    slot_time: time
    slot_end: time
    is_available: bool = True


class ReviewCreate(BaseModel):
    salon_id: UUID
    booking_id: UUID
    master_id: Optional[UUID] = None
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = Field(None, max_length=1000)
    review_photos: Optional[List[str]] = None


class ReviewResponse(BaseModel):
    id: UUID
    rating: int
    review_text: Optional[str]
    created_at: datetime
    salon_response: Optional[str]

    class Config:
        from_attributes = True
