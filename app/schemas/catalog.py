from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from decimal import Decimal


class CatalogSalonResponse(BaseModel):
    id: UUID
    display_name: str
    slug: str
    description_ru: Optional[str]
    logo_url: Optional[str]
    cover_image_url: Optional[str]
    rating: Decimal
    total_reviews: int
    city: str
    is_promoted: bool = False

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    total_pages: int
