from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal


class SalonCreate(BaseModel):
    business_name: str
    display_name: str
    category_id: UUID
    city: str
    phone: str
    email: EmailStr
    description_ru: Optional[str] = None
    description_kk: Optional[str] = None
    description_en: Optional[str] = None
    website_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None


class SalonUpdate(BaseModel):
    display_name: Optional[str] = None
    description_ru: Optional[str] = None
    description_kk: Optional[str] = None
    description_en: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None


class SalonResponse(BaseModel):
    id: UUID
    business_name: str
    display_name: str
    slug: str
    description_ru: Optional[str]
    description_kk: Optional[str]
    description_en: Optional[str]
    logo_url: Optional[str]
    cover_image_url: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    website_url: Optional[str]
    rating: Decimal
    total_reviews: int
    is_active: bool
    created_at: datetime
    branches: Optional[List['BranchResponse']] = []

    class Config:
        from_attributes = True


class BranchCreate(BaseModel):
    branch_name: str
    display_name: str
    city: str
    street_address: str
    building_number: str
    postal_code: Optional[str] = None
    phone: str
    email: Optional[EmailStr] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    working_hours: Optional[Dict[str, Any]] = None


class BranchResponse(BaseModel):
    id: UUID
    branch_name: str
    display_name: str
    city: str
    street_address: str
    building_number: str
    phone: str
    is_main: bool
    is_active: bool

    class Config:
        from_attributes = True


class ServiceCreate(BaseModel):
    service_name_ru: str
    service_name_kk: Optional[str] = None
    service_name_en: Optional[str] = None
    description_ru: Optional[str] = None
    description_kk: Optional[str] = None
    description_en: Optional[str] = None
    duration_minutes: int = Field(..., ge=15)
    base_price: Decimal = Field(..., gt=0)
    category: Optional[str] = None
    price_tiers: Optional[List[Dict[str, Any]]] = None


class ServiceResponse(BaseModel):
    id: UUID
    service_name_ru: str
    service_name_kk: Optional[str]
    service_name_en: Optional[str]
    description_ru: Optional[str]
    duration_minutes: int
    base_price: Decimal
    category: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
