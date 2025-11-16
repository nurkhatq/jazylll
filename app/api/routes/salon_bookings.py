"""
Salon Booking Management Endpoints

Allows salon owners, managers, and masters to manage bookings
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.db.base import get_db
from app.api.deps import get_current_user, require_salon_staff
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus
from app.models.salon import Salon, Master, Service, SalonBranch
from app.schemas.booking import BookingResponse
from pydantic import BaseModel


router = APIRouter(prefix="/salon-bookings", tags=["Salon Booking Management"])


# =======================================
# SCHEMAS
# =======================================

class BookingStatusUpdate(BaseModel):
    """Schema for updating booking status"""
    status: BookingStatus
    cancellation_reason: Optional[str] = None
    notes_for_master: Optional[str] = None


class BookingStats(BaseModel):
    """Booking statistics for salon"""
    total_bookings: int
    pending_bookings: int
    confirmed_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    no_shows: int
    total_revenue: float
    average_rating: Optional[float]
    completion_rate: float


class DailyBooking(BaseModel):
    """Daily booking summary"""
    date: date
    total_bookings: int
    confirmed: int
    completed: int
    revenue: float


# =======================================
# SALON BOOKING MANAGEMENT
# =======================================

@router.get("/salons/{salon_id}/bookings", response_model=List[BookingResponse])
async def get_salon_bookings(
    request: Request,
    salon_id: UUID,
    status_filter: Optional[BookingStatus] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    master_id: Optional[UUID] = Query(None),
    branch_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all bookings for a salon

    Allows salon owner, managers, and masters to view bookings.
    Masters can only see their own bookings.
    """
    # Check permissions
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Platform admin can see all
    if current_user.role == UserRole.PLATFORM_ADMIN:
        pass
    # Salon owner can see all
    elif salon.owner_id == current_user.id:
        pass
    # Master can only see their own bookings
    elif current_user.role == UserRole.MASTER:
        master = db.query(Master).filter(
            Master.user_id == current_user.id,
            Master.salon_id == salon_id,
            Master.is_active == True
        ).first()
        if not master:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Force filter to master's bookings only
        master_id = master.id
    # Salon manager (future implementation)
    elif current_user.role == UserRole.SALON_MANAGER:
        pass  # TODO: Add manager-salon relationship check
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Build query
    query = db.query(Booking).join(Master).filter(Master.salon_id == salon_id)

    # Apply filters
    if status_filter:
        query = query.filter(Booking.status == status_filter)

    if date_from:
        query = query.filter(Booking.booking_date >= date_from)

    if date_to:
        query = query.filter(Booking.booking_date <= date_to)

    if master_id:
        query = query.filter(Booking.master_id == master_id)

    if branch_id:
        query = query.filter(Booking.branch_id == branch_id)

    # Order by date and time (most recent first)
    query = query.order_by(
        Booking.booking_date.desc(),
        Booking.start_time.desc()
    )

    # Pagination
    total = query.count()
    bookings = query.offset((page - 1) * per_page).limit(per_page).all()

    return bookings


@router.patch("/salons/{salon_id}/bookings/{booking_id}/status", response_model=BookingResponse)
async def update_booking_status(
    request: Request,
    salon_id: UUID,
    booking_id: UUID,
    status_update: BookingStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update booking status

    Salon staff can:
    - Confirm bookings (PENDING -> CONFIRMED)
    - Start service (CONFIRMED -> IN_PROGRESS)
    - Complete bookings (IN_PROGRESS -> COMPLETED)
    - Cancel bookings (ANY -> CANCELLED_BY_SALON)
    """
    # Get booking
    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Verify booking belongs to this salon
    master = db.query(Master).filter(Master.id == booking.master_id).first()
    if not master or master.salon_id != salon_id:
        raise HTTPException(status_code=404, detail="Booking not found in this salon")

    # Check permissions
    salon = db.query(Salon).filter(Salon.id == salon_id).first()

    is_owner = salon.owner_id == current_user.id
    is_admin = current_user.role == UserRole.PLATFORM_ADMIN
    is_assigned_master = False

    if current_user.role == UserRole.MASTER:
        assigned_master = db.query(Master).filter(
            Master.user_id == current_user.id,
            Master.id == booking.master_id
        ).first()
        is_assigned_master = assigned_master is not None

    if not (is_owner or is_admin or is_assigned_master):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate status transitions
    current_status = booking.status
    new_status = status_update.status

    # Define allowed transitions
    allowed_transitions = {
        BookingStatus.PENDING: [BookingStatus.CONFIRMED, BookingStatus.CANCELLED_BY_SALON],
        BookingStatus.CONFIRMED: [BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED_BY_SALON, BookingStatus.NO_SHOW],
        BookingStatus.IN_PROGRESS: [BookingStatus.COMPLETED, BookingStatus.CANCELLED_BY_SALON],
        # Completed and cancelled are final states
        BookingStatus.COMPLETED: [],
        BookingStatus.CANCELLED_BY_CLIENT: [],
        BookingStatus.CANCELLED_BY_SALON: [],
        BookingStatus.NO_SHOW: [],
    }

    if new_status not in allowed_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {current_status.value} to {new_status.value}"
        )

    # Update booking
    booking.status = new_status

    if new_status == BookingStatus.CANCELLED_BY_SALON:
        booking.cancelled_at = datetime.utcnow()
        if status_update.cancellation_reason:
            booking.cancellation_reason = status_update.cancellation_reason

        # Send cancellation notification to client
        if booking.client and booking.client.phone:
            from app.core.whatsapp import whatsapp_client
            try:
                message = f"""Ваша запись отменена ❌

Салон: {salon.display_name}
Дата: {booking.booking_date.strftime('%d.%m.%Y')}
Время: {booking.start_time.strftime('%H:%M')}

Причина: {status_update.cancellation_reason or 'Не указана'}

Приносим извинения за неудобства."""
                await whatsapp_client._send_message(booking.client.phone, message)
            except Exception as e:
                print(f"⚠️  Failed to send cancellation notification: {e}")

    elif new_status == BookingStatus.COMPLETED:
        booking.completed_at = datetime.utcnow()

    if status_update.notes_for_master:
        booking.notes_for_master = status_update.notes_for_master

    db.commit()
    db.refresh(booking)

    return booking


@router.get("/salons/{salon_id}/stats", response_model=BookingStats)
async def get_salon_booking_stats(
    request: Request,
    salon_id: UUID,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get booking statistics for salon

    Returns comprehensive statistics including:
    - Booking counts by status
    - Total revenue
    - Average rating
    - Completion rate
    """
    # Check permissions - salon owner, manager, or admin
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    if not (
        salon.owner_id == current_user.id or
        current_user.role in [UserRole.PLATFORM_ADMIN, UserRole.SALON_MANAGER]
    ):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Build base query
    query = db.query(Booking).join(Master).filter(Master.salon_id == salon_id)

    # Apply date filters
    if date_from:
        query = query.filter(Booking.booking_date >= date_from)
    if date_to:
        query = query.filter(Booking.booking_date <= date_to)

    # Get counts by status
    all_bookings = query.all()
    total_bookings = len(all_bookings)

    pending = sum(1 for b in all_bookings if b.status == BookingStatus.PENDING)
    confirmed = sum(1 for b in all_bookings if b.status == BookingStatus.CONFIRMED)
    completed = sum(1 for b in all_bookings if b.status == BookingStatus.COMPLETED)
    cancelled = sum(
        1 for b in all_bookings
        if b.status in [BookingStatus.CANCELLED_BY_CLIENT, BookingStatus.CANCELLED_BY_SALON]
    )
    no_shows = sum(1 for b in all_bookings if b.status == BookingStatus.NO_SHOW)

    # Calculate revenue (from completed bookings)
    total_revenue = sum(
        float(b.final_price) for b in all_bookings
        if b.status == BookingStatus.COMPLETED
    )

    # Calculate completion rate
    completable_bookings = completed + cancelled + no_shows
    completion_rate = (completed / completable_bookings * 100) if completable_bookings > 0 else 0

    # Get average rating from reviews
    from app.models.booking import Review
    avg_rating_result = db.query(func.avg(Review.rating)).filter(
        Review.salon_id == salon_id,
        Review.is_visible == True
    ).scalar()
    average_rating = float(avg_rating_result) if avg_rating_result else None

    return BookingStats(
        total_bookings=total_bookings,
        pending_bookings=pending,
        confirmed_bookings=confirmed,
        completed_bookings=completed,
        cancelled_bookings=cancelled,
        no_shows=no_shows,
        total_revenue=total_revenue,
        average_rating=average_rating,
        completion_rate=round(completion_rate, 2)
    )


@router.get("/salons/{salon_id}/stats/daily", response_model=List[DailyBooking])
async def get_daily_booking_stats(
    request: Request,
    salon_id: UUID,
    date_from: date = Query(...),
    date_to: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get daily booking statistics for salon

    Returns day-by-day breakdown of bookings and revenue
    """
    # Check permissions
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    if not (
        salon.owner_id == current_user.id or
        current_user.role in [UserRole.PLATFORM_ADMIN, UserRole.SALON_MANAGER]
    ):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate date range
    if date_to < date_from:
        raise HTTPException(status_code=400, detail="date_to must be after date_from")

    if (date_to - date_from).days > 90:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")

    # Get bookings in date range
    bookings = db.query(Booking).join(Master).filter(
        Master.salon_id == salon_id,
        Booking.booking_date >= date_from,
        Booking.booking_date <= date_to
    ).all()

    # Group by date
    daily_stats = {}
    current_date = date_from

    while current_date <= date_to:
        daily_bookings = [b for b in bookings if b.booking_date == current_date]

        confirmed_count = sum(
            1 for b in daily_bookings
            if b.status in [BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS, BookingStatus.COMPLETED]
        )
        completed_count = sum(1 for b in daily_bookings if b.status == BookingStatus.COMPLETED)
        revenue = sum(float(b.final_price) for b in daily_bookings if b.status == BookingStatus.COMPLETED)

        daily_stats[current_date] = DailyBooking(
            date=current_date,
            total_bookings=len(daily_bookings),
            confirmed=confirmed_count,
            completed=completed_count,
            revenue=revenue
        )

        current_date += timedelta(days=1)

    return list(daily_stats.values())


@router.get("/my-bookings", response_model=List[BookingResponse])
async def get_master_bookings(
    request: Request,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status_filter: Optional[BookingStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get bookings for current master

    Masters can view only their own bookings
    """
    # Only masters can use this endpoint
    if current_user.role != UserRole.MASTER:
        raise HTTPException(status_code=403, detail="Only masters can access this endpoint")

    # Find master profile
    master = db.query(Master).filter(
        Master.user_id == current_user.id,
        Master.is_active == True
    ).first()

    if not master:
        raise HTTPException(status_code=404, detail="Master profile not found")

    # Build query
    query = db.query(Booking).filter(Booking.master_id == master.id)

    # Apply filters
    if date_from:
        query = query.filter(Booking.booking_date >= date_from)
    if date_to:
        query = query.filter(Booking.booking_date <= date_to)
    if status_filter:
        query = query.filter(Booking.status == status_filter)

    # Order by date
    bookings = query.order_by(
        Booking.booking_date.desc(),
        Booking.start_time.desc()
    ).all()

    return bookings
