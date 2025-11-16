from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List
from uuid import UUID

from app.db.base import get_db
from app.models.salon import SalonCategory, Salon, SalonBranch

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[dict])
async def get_all_categories(
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db),
):
    """
    Get all salon categories (PUBLIC - no auth required)

    This is used for:
    - Homepage category selection
    - Filter dropdowns
    - Navigation menus
    """
    categories = (
        db.query(SalonCategory)
        .filter(SalonCategory.is_active == is_active)
        .order_by(SalonCategory.sort_order)
        .all()
    )

    result = []
    for category in categories:
        # Count active salons in this category
        salon_count = (
            db.query(Salon)
            .filter(
                Salon.category_id == category.id,
                Salon.is_active == True,
                Salon.is_visible_in_catalog == True,
                Salon.deleted_at.is_(None),
            )
            .count()
        )

        result.append(
            {
                "id": str(category.id),
                "code": category.code,
                "name_ru": category.name_ru,
                "name_kk": category.name_kk,
                "name_en": category.name_en,
                "description_ru": category.description_ru,
                "description_kk": category.description_kk,
                "description_en": category.description_en,
                "icon_url": category.icon_url,
                "salon_count": salon_count,
            }
        )

    return result


@router.get("/{category_id}")
async def get_category_by_id(
    category_id: UUID,
    db: Session = Depends(get_db),
):
    """Get single category details (PUBLIC)"""
    category = db.query(SalonCategory).filter(SalonCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Count salons
    salon_count = (
        db.query(Salon)
        .filter(
            Salon.category_id == category.id,
            Salon.is_active == True,
            Salon.is_visible_in_catalog == True,
            Salon.deleted_at.is_(None),
        )
        .count()
    )

    return {
        "id": str(category.id),
        "code": category.code,
        "name_ru": category.name_ru,
        "name_kk": category.name_kk,
        "name_en": category.name_en,
        "description_ru": category.description_ru,
        "description_kk": category.description_kk,
        "description_en": category.description_en,
        "icon_url": category.icon_url,
        "salon_count": salon_count,
    }


@router.get("/cities/list")
async def get_cities_with_salons(
    category_id: UUID = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
):
    """
    Get list of cities that have salons (PUBLIC)

    Used for location filters in catalog
    """
    query = (
        db.query(distinct(SalonBranch.city))
        .join(Salon, SalonBranch.salon_id == Salon.id)
        .filter(
            Salon.is_active == True,
            Salon.is_visible_in_catalog == True,
            Salon.deleted_at.is_(None),
            SalonBranch.is_active == True,
        )
    )

    # Filter by category if specified
    if category_id:
        query = query.filter(Salon.category_id == category_id)

    cities = query.order_by(SalonBranch.city).all()

    # Count salons per city
    result = []
    for (city,) in cities:
        count_query = (
            db.query(Salon.id)
            .join(SalonBranch, Salon.id == SalonBranch.salon_id)
            .filter(
                SalonBranch.city == city,
                Salon.is_active == True,
                Salon.is_visible_in_catalog == True,
                Salon.deleted_at.is_(None),
            )
        )

        if category_id:
            count_query = count_query.filter(Salon.category_id == category_id)

        salon_count = count_query.distinct().count()

        result.append({"city": city, "salon_count": salon_count})

    return result
