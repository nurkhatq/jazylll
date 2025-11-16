from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date, time, datetime, timedelta
from decimal import Decimal

from app.db.base import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.booking import Booking, BookingStatus, BookingCreatedVia, Review
from app.models.salon import Master, Service, MasterSchedule, ScheduleException, MasterService, Salon
from app.schemas.booking import BookingCreate, BookingResponse, AvailableSlot, ReviewCreate, ReviewResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def calculate_available_slots(
    db: Session,
    master_id: UUID,
    service_id: UUID,
    branch_id: UUID,
    booking_date: date,
) -> List[AvailableSlot]:
    """Calculate available time slots for a master on a given date"""
    # Get service duration
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        return []

    duration_minutes = service.duration_minutes

    # Get day of week (1=Monday, 7=Sunday)
    day_of_week = booking_date.isoweekday()

    # Check for exceptions first
    exception = (
        db.query(ScheduleException)
        .filter(ScheduleException.master_id == master_id, ScheduleException.exception_date == booking_date)
        .first()
    )

    if exception:
        if exception.exception_type == "day_off" or exception.exception_type == "fully_booked":
            return []
        elif exception.exception_type == "custom_hours":
            work_start = exception.custom_start_time
            work_end = exception.custom_end_time
            breaks = []
    else:
        # Get regular schedule
        schedule = (
            db.query(MasterSchedule)
            .filter(
                MasterSchedule.master_id == master_id,
                MasterSchedule.branch_id == branch_id,
                MasterSchedule.day_of_week == day_of_week,
            )
            .first()
        )

        if not schedule or not schedule.is_working:
            return []

        work_start = schedule.start_time
        work_end = schedule.end_time
        breaks = schedule.breaks or []

    # Get existing bookings for this master on this date
    existing_bookings = (
        db.query(Booking)
        .filter(
            Booking.master_id == master_id,
            Booking.booking_date == booking_date,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS]),
        )
        .all()
    )

    # Generate time slots (15-minute intervals)
    slots = []
    current_datetime = datetime.combine(booking_date, work_start)
    end_datetime = datetime.combine(booking_date, work_end)
    slot_interval = timedelta(minutes=15)
    service_duration = timedelta(minutes=duration_minutes)
    buffer_time = timedelta(minutes=5)

    while current_datetime + service_duration <= end_datetime:
        slot_start_time = current_datetime.time()
        slot_end_time = (current_datetime + service_duration).time()

        # Check if slot is in the future (at least 1 hour from now for online bookings)
        now = datetime.now()
        slot_datetime = datetime.combine(booking_date, slot_start_time)
        if slot_datetime < now + timedelta(hours=1):
            current_datetime += slot_interval
            continue

        # Check if slot overlaps with breaks
        is_break = False
        for break_period in breaks:
            break_start = datetime.strptime(break_period.get("break_start"), "%H:%M").time()
            break_end = datetime.strptime(break_period.get("break_end"), "%H:%M").time()
            if not (slot_end_time <= break_start or slot_start_time >= break_end):
                is_break = True
                break

        if is_break:
            current_datetime += slot_interval
            continue

        # Check if slot overlaps with existing bookings
        is_booked = False
        for booking in existing_bookings:
            booking_start_datetime = datetime.combine(booking.booking_date, booking.start_time)
            booking_end_datetime = datetime.combine(booking.booking_date, booking.end_time) + buffer_time

            slot_start_datetime = datetime.combine(booking_date, slot_start_time)
            slot_end_datetime = datetime.combine(booking_date, slot_end_time)

            if not (slot_end_datetime <= booking_start_datetime or slot_start_datetime >= booking_end_datetime):
                is_booked = True
                break

        if not is_booked:
            slots.append(AvailableSlot(slot_time=slot_start_time, slot_end=slot_end_time))

        current_datetime += slot_interval

    return slots


@router.get("/masters/{master_id}/available-slots", response_model=List[AvailableSlot])
async def get_available_slots(
    master_id: UUID,
    date: date = Query(...),
    service_id: UUID = Query(...),
    branch_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    """Get available booking slots for a master"""
    master = db.query(Master).filter(Master.id == master_id).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    slots = calculate_available_slots(db, master_id, service_id, branch_id, date)
    return slots


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create new booking"""
    # Validate master exists and is active
    master = db.query(Master).filter(Master.id == booking_data.master_id, Master.is_active == True).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found or inactive")

    # Validate service exists and is active
    service = db.query(Service).filter(Service.id == booking_data.service_id, Service.is_active == True).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found or inactive")

    # Check if selected slot is available
    available_slots = calculate_available_slots(
        db, booking_data.master_id, booking_data.service_id, booking_data.branch_id, booking_data.booking_date
    )

    slot_available = any(
        slot.slot_time == booking_data.start_time for slot in available_slots
    )

    if not slot_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Selected time slot is no longer available",
        )

    # Calculate end time
    end_time = (
        datetime.combine(booking_data.booking_date, booking_data.start_time)
        + timedelta(minutes=service.duration_minutes)
    ).time()

    # Determine price (use custom price if set for master, otherwise base price)
    master_service = (
        db.query(MasterService)
        .filter(
            MasterService.master_id == booking_data.master_id,
            MasterService.service_id == booking_data.service_id,
        )
        .first()
    )

    if master_service and master_service.custom_price:
        final_price = master_service.custom_price
    else:
        final_price = service.base_price

    # Create booking
    booking = Booking(
        client_id=current_user.id,
        master_id=booking_data.master_id,
        service_id=booking_data.service_id,
        branch_id=booking_data.branch_id,
        booking_date=booking_data.booking_date,
        start_time=booking_data.start_time,
        end_time=end_time,
        final_price=final_price,
        status=BookingStatus.PENDING,
        created_via=BookingCreatedVia.MOBILE_APP,
        notes_from_client=booking_data.notes_from_client,
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    # TODO: Queue WhatsApp notification to client and master

    return booking


@router.get("", response_model=List[BookingResponse])
async def get_bookings(
    current_user: User = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    """Get user's bookings"""
    query = db.query(Booking).filter(Booking.client_id == current_user.id)

    if status_filter:
        query = query.filter(Booking.status == status_filter)

    bookings = query.order_by(Booking.booking_date.desc(), Booking.start_time.desc()).all()
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get booking details"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Check permissions
    if booking.client_id != current_user.id:
        # TODO: Also allow salon staff to view
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return booking


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: UUID,
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update booking status"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Check permissions
    if booking.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Validate status transition (clients can only cancel)
    if status == "cancelled_by_client":
        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise HTTPException(status_code=400, detail="Cannot cancel booking in current status")
        booking.status = BookingStatus.CANCELLED_BY_CLIENT
        booking.cancelled_at = datetime.utcnow()
    else:
        raise HTTPException(status_code=400, detail="Invalid status transition")

    db.commit()
    db.refresh(booking)

    return booking


# Reviews
@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create review for completed booking"""
    # Validate booking exists and belongs to current user
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == review_data.booking_id,
            Booking.client_id == current_user.id,
            Booking.status == BookingStatus.COMPLETED,
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found or not eligible for review",
        )

    # Check if review already exists
    existing_review = db.query(Review).filter(Review.booking_id == review_data.booking_id).first()
    if existing_review:
        raise HTTPException(status_code=409, detail="Review already exists for this booking")

    # Create review
    review = Review(
        booking_id=review_data.booking_id,
        client_id=current_user.id,
        salon_id=review_data.salon_id,
        master_id=review_data.master_id,
        rating=review_data.rating,
        review_text=review_data.review_text,
        review_photos=review_data.review_photos,
        is_verified=True,
        is_visible=True,
    )

    db.add(review)

    # Update salon rating
    salon = db.query(Salon).filter(Salon.id == review_data.salon_id).first()
    if salon:
        all_reviews = db.query(Review).filter(Review.salon_id == review_data.salon_id, Review.is_visible == True).all()
        total_rating = sum(r.rating for r in all_reviews) + review_data.rating
        salon.total_reviews = len(all_reviews) + 1
        salon.rating = Decimal(total_rating) / Decimal(salon.total_reviews)

    # Update master rating if applicable
    if review_data.master_id:
        master = db.query(Master).filter(Master.id == review_data.master_id).first()
        if master:
            master_reviews = (
                db.query(Review)
                .filter(Review.master_id == review_data.master_id, Review.is_visible == True)
                .all()
            )
            total_rating = sum(r.rating for r in master_reviews) + review_data.rating
            master.total_reviews = len(master_reviews) + 1
            master.rating = Decimal(total_rating) / Decimal(master.total_reviews)

    db.commit()
    db.refresh(review)

    return review


@router.get("/reviews", response_model=List[ReviewResponse])
async def get_reviews(
    salon_id: Optional[UUID] = Query(None),
    master_id: Optional[UUID] = Query(None),
    rating: Optional[int] = Query(None, ge=1, le=5),
    sort: str = Query("recent", description="Sort by: recent, highest_rated, lowest_rated"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get list of reviews"""
    # Must provide either salon_id or master_id
    if not salon_id and not master_id:
        raise HTTPException(status_code=400, detail="Must provide salon_id or master_id")

    query = db.query(Review).filter(Review.is_visible == True)

    if salon_id:
        query = query.filter(Review.salon_id == salon_id)
    if master_id:
        query = query.filter(Review.master_id == master_id)
    if rating:
        query = query.filter(Review.rating == rating)

    # Apply sorting
    if sort == "highest_rated":
        query = query.order_by(Review.rating.desc())
    elif sort == "lowest_rated":
        query = query.order_by(Review.rating.asc())
    else:  # recent
        query = query.order_by(Review.created_at.desc())

    # Pagination
    total = query.count()
    reviews = query.offset((page - 1) * per_page).limit(per_page).all()

    return reviews


@router.post("/reviews/{review_id}/response", response_model=ReviewResponse)
async def add_salon_response(
    review_id: UUID,
    response_text: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add salon response to a review"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Check permissions - must be owner or manager of the salon
    salon = db.query(Salon).filter(Salon.id == review.salon_id).first()
    if salon.owner_id != current_user.id and current_user.role not in [
        UserRole.PLATFORM_ADMIN,
        UserRole.SALON_MANAGER,
    ]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Check if response already exists
    if review.salon_response:
        raise HTTPException(status_code=400, detail="Response already exists for this review")

    # Add response
    review.salon_response = response_text
    review.responded_at = datetime.utcnow()

    db.commit()
    db.refresh(review)

    # TODO: Send notification to client

    return review


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def hide_review(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hide a review (admin only)"""
    # Only platform admins can hide reviews
    if current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Only platform admins can hide reviews")

    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Hide review
    review.is_visible = False
    db.commit()

    return None
