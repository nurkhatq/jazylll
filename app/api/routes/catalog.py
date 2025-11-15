from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
import math

from app.db.base import get_db
from app.models.salon import Salon, SalonBranch, SalonCategory
from app.models.catalog import CatalogImpression, CatalogClick
from app.schemas.catalog import CatalogSalonResponse, PaginatedResponse

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("/salons")
async def get_catalog_salons(
    category_id: UUID = Query(..., description="Category ID (required)"),
    city: Optional[str] = Query(None, description="Filter by city"),
    search: Optional[str] = Query(None, description="Search query"),
    sort: str = Query("relevance", description="Sort by: relevance, rating, recent"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get paginated list of salons in catalog"""
    # Base query
    query = db.query(Salon).filter(
        Salon.category_id == category_id,
        Salon.is_active == True,
        Salon.is_visible_in_catalog == True,
        Salon.deleted_at.is_(None),
    )

    # Apply city filter
    if city:
        branch_ids = (
            db.query(SalonBranch.salon_id).filter(SalonBranch.city == city, SalonBranch.is_active == True).all()
        )
        salon_ids = [b[0] for b in branch_ids]
        query = query.filter(Salon.id.in_(salon_ids))

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Salon.display_name.ilike(search_pattern),
                Salon.description_ru.ilike(search_pattern),
                Salon.description_kk.ilike(search_pattern),
                Salon.description_en.ilike(search_pattern),
            )
        )

    # Separate promoted and organic salons
    promoted_query = query.filter(Salon.auction_bid > 0, Salon.advertising_budget > 0)
    organic_query = query.filter(or_(Salon.auction_bid == 0, Salon.advertising_budget == 0))

    # Sort promoted salons by bid (descending)
    promoted_salons = promoted_query.order_by(Salon.auction_bid.desc()).all()

    # Sort organic salons by algorithm
    if sort == "rating":
        organic_salons = organic_query.order_by(Salon.rating.desc(), Salon.total_reviews.desc()).all()
    elif sort == "recent":
        organic_salons = organic_query.order_by(Salon.created_at.desc()).all()
    else:  # relevance (composite algorithm)
        # Simplified relevance: rating * 0.4 + normalized reviews * 0.3 + recency * 0.3
        organic_salons = organic_query.order_by(
            Salon.rating.desc(),
            Salon.total_reviews.desc(),
            Salon.updated_at.desc(),
        ).all()

    # Interleave promoted and organic (1 promoted : 3 organic)
    final_salons = []
    promoted_index = 0
    organic_index = 0

    while promoted_index < len(promoted_salons) or organic_index < len(organic_salons):
        # Add 1 promoted
        if promoted_index < len(promoted_salons):
            salon = promoted_salons[promoted_index]
            final_salons.append((salon, True))  # (salon, is_promoted)
            promoted_index += 1

        # Add up to 3 organic
        for _ in range(3):
            if organic_index < len(organic_salons):
                salon = organic_salons[organic_index]
                final_salons.append((salon, False))
                organic_index += 1

    # Pagination
    total = len(final_salons)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_salons = final_salons[start:end]

    # Log impressions
    current_hour = datetime.utcnow().hour
    current_date = date.today()
    for position, (salon, is_promoted) in enumerate(paginated_salons, start=start + 1):
        # Calculate cost for promoted salons
        cost = Decimal("0")
        if is_promoted:
            # Impression cost is typically lower, e.g., 10% of click cost
            cost = salon.auction_bid * Decimal("0.1")

        impression = CatalogImpression(
            salon_id=salon.id,
            impression_date=current_date,
            impression_hour=current_hour,
            position=position,
            is_promoted=is_promoted,
            cost=cost,
        )
        db.add(impression)

    db.commit()

    # Get main branch city for each salon
    salon_responses = []
    for salon, is_promoted in paginated_salons:
        main_branch = (
            db.query(SalonBranch).filter(SalonBranch.salon_id == salon.id, SalonBranch.is_main == True).first()
        )

        salon_responses.append(
            {
                "id": salon.id,
                "display_name": salon.display_name,
                "slug": salon.slug,
                "description_ru": salon.description_ru,
                "logo_url": salon.logo_url,
                "cover_image_url": salon.cover_image_url,
                "rating": salon.rating,
                "total_reviews": salon.total_reviews,
                "city": main_branch.city if main_branch else "Unknown",
                "is_promoted": is_promoted,
            }
        )

    return {
        "items": salon_responses,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total / per_page),
    }


@router.post("/salons/{salon_id}/click", status_code=204)
async def register_salon_click(
    salon_id: UUID,
    session_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """Register click on salon in catalog"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Determine if this was a promoted click
    is_promoted = salon.auction_bid > 0 and salon.advertising_budget > 0

    # Calculate click cost (50% of bid)
    cost = Decimal("0")
    if is_promoted:
        cost = salon.auction_bid * Decimal("0.5")

        # Deduct from advertising budget
        if salon.advertising_budget >= cost:
            salon.advertising_budget -= cost
        else:
            # Insufficient budget, set bid to 0
            salon.auction_bid = Decimal("0")
            cost = Decimal("0")

    # Register click
    click = CatalogClick(
        salon_id=salon_id,
        clicked_at=datetime.utcnow(),
        is_promoted=is_promoted,
        cost=cost,
        session_id=session_id,
    )
    db.add(click)
    db.commit()

    return None


@router.get("/salons/{salon_slug}")
async def get_salon_public_page(salon_slug: str, db: Session = Depends(get_db)):
    """Get public page data for salon"""
    salon = db.query(Salon).filter(Salon.slug == salon_slug, Salon.deleted_at.is_(None)).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Get branches
    branches = db.query(SalonBranch).filter(SalonBranch.salon_id == salon.id, SalonBranch.is_active == True).all()

    # Get category
    category = db.query(SalonCategory).filter(SalonCategory.id == salon.category_id).first()

    return {
        "id": salon.id,
        "display_name": salon.display_name,
        "slug": salon.slug,
        "description_ru": salon.description_ru,
        "description_kk": salon.description_kk,
        "description_en": salon.description_en,
        "logo_url": salon.logo_url,
        "cover_image_url": salon.cover_image_url,
        "phone": salon.phone,
        "email": salon.email,
        "website_url": salon.website_url,
        "social_links": salon.social_links,
        "rating": float(salon.rating),
        "total_reviews": salon.total_reviews,
        "category": {
            "id": category.id,
            "name_ru": category.name_ru,
            "name_kk": category.name_kk,
            "name_en": category.name_en,
        }
        if category
        else None,
        "branches": [
            {
                "id": branch.id,
                "display_name": branch.display_name,
                "city": branch.city,
                "address": f"{branch.street_address}, {branch.building_number}",
                "phone": branch.phone,
                "working_hours": branch.working_hours,
            }
            for branch in branches
        ],
        "salon_website_url": f"https://{salon.slug}.jazyl.tech",
    }
