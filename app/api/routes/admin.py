from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel

from app.db.base import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.salon import Salon, SalonCategory, SubscriptionPlan, Master
from app.models.booking import Booking, BookingStatus, Review
from app.models.payment import Payment, PaymentType, PaymentStatus

router = APIRouter(prefix="/admin", tags=["Admin"])


# Admin-only dependency
def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class SalonAdminUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_visible_in_catalog: Optional[bool] = None
    subscription_plan_id: Optional[UUID] = None
    subscription_end_date: Optional[date] = None
    notes: Optional[str] = None


@router.get("/salons")
async def list_all_salons(
    category_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_visible_in_catalog: Optional[bool] = Query(None),
    subscription_status: Optional[str] = Query(None, description="active, expired, trial"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get list of all salons (admin only)"""
    query = db.query(Salon).filter(Salon.deleted_at.is_(None))

    # Apply filters
    if category_id:
        query = query.filter(Salon.category_id == category_id)
    if is_active is not None:
        query = query.filter(Salon.is_active == is_active)
    if is_visible_in_catalog is not None:
        query = query.filter(Salon.is_visible_in_catalog == is_visible_in_catalog)

    # Subscription status filter
    today = date.today()
    if subscription_status == "active":
        query = query.filter(
            Salon.subscription_end_date >= today, Salon.is_active == True
        )
    elif subscription_status == "expired":
        query = query.filter(Salon.subscription_end_date < today)
    elif subscription_status == "trial":
        trial_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.plan_code == "trial").first()
        if trial_plan:
            query = query.filter(Salon.subscription_plan_id == trial_plan.id)

    # Search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.join(User, Salon.owner_id == User.id).filter(
            or_(
                Salon.display_name.ilike(search_pattern),
                Salon.business_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )

    # Pagination
    total = query.count()
    salons = query.order_by(Salon.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    # Build response
    salon_list = []
    for salon in salons:
        # Get category
        category = db.query(SalonCategory).filter(SalonCategory.id == salon.category_id).first()

        # Get master count
        master_count = db.query(Master).filter(Master.salon_id == salon.id, Master.is_active == True).count()

        # Get booking count this month
        first_day = date.today().replace(day=1)
        booking_count = (
            db.query(Booking)
            .filter(Booking.booking_date >= first_day)
            .join(Master, Booking.master_id == Master.id)
            .filter(Master.salon_id == salon.id)
            .count()
        )

        salon_list.append(
            {
                "id": str(salon.id),
                "display_name": salon.display_name,
                "business_name": salon.business_name,
                "slug": salon.slug,
                "owner": {
                    "id": str(salon.owner.id),
                    "email": salon.owner.email,
                    "name": f"{salon.owner.first_name or ''} {salon.owner.last_name or ''}".strip(),
                },
                "category": {
                    "id": str(category.id),
                    "name": category.name_en,
                } if category else None,
                "subscription": {
                    "plan_code": salon.subscription_plan.plan_code if salon.subscription_plan else None,
                    "start_date": str(salon.subscription_start_date) if salon.subscription_start_date else None,
                    "end_date": str(salon.subscription_end_date) if salon.subscription_end_date else None,
                    "is_expired": salon.subscription_end_date < today if salon.subscription_end_date else False,
                },
                "is_active": salon.is_active,
                "is_visible_in_catalog": salon.is_visible_in_catalog,
                "statistics": {
                    "total_masters": master_count,
                    "bookings_this_month": booking_count,
                    "total_reviews": salon.total_reviews,
                    "rating": float(salon.rating),
                },
                "created_at": str(salon.created_at),
            }
        )

    return {
        "items": salon_list,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.patch("/salons/{salon_id}")
async def manage_salon(
    salon_id: UUID,
    update_data: SalonAdminUpdate,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Manage salon (admin only)"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Update fields
    if update_data.is_active is not None:
        salon.is_active = update_data.is_active
    if update_data.is_visible_in_catalog is not None:
        salon.is_visible_in_catalog = update_data.is_visible_in_catalog
    if update_data.subscription_plan_id:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == update_data.subscription_plan_id).first()
        if not plan:
            raise HTTPException(status_code=400, detail="Invalid subscription plan")
        salon.subscription_plan_id = update_data.subscription_plan_id
    if update_data.subscription_end_date:
        salon.subscription_end_date = update_data.subscription_end_date

    db.commit()

    # TODO: Log change in audit_logs

    return {
        "id": str(salon.id),
        "display_name": salon.display_name,
        "is_active": salon.is_active,
        "is_visible_in_catalog": salon.is_visible_in_catalog,
        "message": "Salon updated successfully",
    }


@router.get("/statistics")
async def get_platform_statistics(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get platform-wide statistics (admin only)"""
    # Default to current month
    if not date_from:
        date_from = date.today().replace(day=1)
    if not date_to:
        date_to = date.today()

    # Total salons
    total_salons = db.query(Salon).filter(Salon.deleted_at.is_(None)).count()
    active_salons = db.query(Salon).filter(Salon.is_active == True, Salon.deleted_at.is_(None)).count()

    # Salons by category
    salons_by_category = {}
    categories = db.query(SalonCategory).filter(SalonCategory.is_active == True).all()
    for category in categories:
        count = db.query(Salon).filter(Salon.category_id == category.id, Salon.deleted_at.is_(None)).count()
        salons_by_category[category.name_en] = count

    # Total masters
    total_masters = db.query(Master).filter(Master.is_active == True).count()

    # Total clients
    total_clients = db.query(User).filter(User.role == UserRole.CLIENT).count()

    # Bookings
    total_bookings = db.query(Booking).count()
    bookings_this_month = (
        db.query(Booking)
        .filter(Booking.booking_date >= date_from, Booking.booking_date <= date_to)
        .count()
    )

    completed_bookings = (
        db.query(Booking)
        .filter(
            Booking.booking_date >= date_from,
            Booking.booking_date <= date_to,
            Booking.status == BookingStatus.COMPLETED,
        )
        .count()
    )

    total_bookings_in_period = (
        db.query(Booking)
        .filter(Booking.booking_date >= date_from, Booking.booking_date <= date_to)
        .count()
    )

    completed_rate = (
        (completed_bookings / total_bookings_in_period * 100) if total_bookings_in_period > 0 else 0
    )

    # Reviews
    total_reviews = db.query(Review).filter(Review.is_visible == True).count()

    # Average platform rating
    avg_rating = db.query(func.avg(Salon.rating)).scalar() or Decimal("0")

    # Revenue (this period)
    subscription_payments = (
        db.query(func.sum(Payment.amount))
        .filter(
            Payment.payment_type == PaymentType.SUBSCRIPTION,
            Payment.payment_status == PaymentStatus.COMPLETED,
            Payment.completed_at >= datetime.combine(date_from, datetime.min.time()),
            Payment.completed_at <= datetime.combine(date_to, datetime.max.time()),
        )
        .scalar()
        or Decimal("0")
    )

    advertising_payments = (
        db.query(func.sum(Payment.amount))
        .filter(
            Payment.payment_type == PaymentType.ADVERTISING_BUDGET,
            Payment.payment_status == PaymentStatus.COMPLETED,
            Payment.completed_at >= datetime.combine(date_from, datetime.min.time()),
            Payment.completed_at <= datetime.combine(date_to, datetime.max.time()),
        )
        .scalar()
        or Decimal("0")
    )

    total_revenue = subscription_payments + advertising_payments

    # Calculate growth rate (compare to previous period)
    period_days = (date_to - date_from).days + 1
    prev_date_from = date_from - timedelta(days=period_days)
    prev_date_to = date_from - timedelta(days=1)

    prev_revenue = (
        db.query(func.sum(Payment.amount))
        .filter(
            Payment.payment_status == PaymentStatus.COMPLETED,
            Payment.completed_at >= datetime.combine(prev_date_from, datetime.min.time()),
            Payment.completed_at <= datetime.combine(prev_date_to, datetime.max.time()),
        )
        .scalar()
        or Decimal("0")
    )

    growth_rate = (
        ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    )

    return {
        "date_from": str(date_from),
        "date_to": str(date_to),
        "total_salons": total_salons,
        "active_salons": active_salons,
        "salons_by_category": salons_by_category,
        "total_masters": total_masters,
        "total_clients": total_clients,
        "total_bookings": total_bookings,
        "bookings_this_month": bookings_this_month,
        "completed_bookings_rate": round(completed_rate, 2),
        "total_reviews": total_reviews,
        "average_platform_rating": round(float(avg_rating), 2),
        "revenue": {
            "subscription_revenue": float(subscription_payments),
            "advertising_revenue": float(advertising_payments),
            "total_revenue": float(total_revenue),
            "growth_rate": round(float(growth_rate), 2),
        },
    }


@router.get("/reviews/moderation")
async def get_reviews_for_moderation(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get reviews requiring moderation (admin only)"""
    # For now, show all visible reviews sorted by recent
    # In production, this would filter by moderation flags
    query = db.query(Review).filter(Review.is_visible == True)

    total = query.count()
    reviews = query.order_by(Review.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    review_list = []
    for review in reviews:
        salon = db.query(Salon).filter(Salon.id == review.salon_id).first()
        client = db.query(User).filter(User.id == review.client_id).first()

        review_list.append(
            {
                "id": str(review.id),
                "client": {
                    "id": str(client.id),
                    "name": f"{client.first_name or ''} {client.last_name or ''}".strip(),
                    "phone": client.phone,
                },
                "salon": {
                    "id": str(salon.id),
                    "name": salon.display_name,
                },
                "rating": review.rating,
                "review_text": review.review_text,
                "created_at": str(review.created_at),
                "is_visible": review.is_visible,
                "salon_response": review.salon_response,
                "moderation_reason": None,  # TODO: Implement auto-moderation flags
            }
        )

    return {
        "items": review_list,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }
