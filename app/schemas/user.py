from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    id: UUID
    phone: Optional[str]
    phone_verified: bool
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    email: Optional[str]
    role: str
    photo_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
