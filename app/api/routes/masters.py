from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import secrets
import os
import uuid as uuid_lib

from app.db.base import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.salon import (
    Master,
    MasterTier,
    MasterBranch,
    MasterService,
    MasterSchedule,
    ScheduleException,
    ExceptionType,
    Salon,
    SalonBranch,
    Service,
)
from app.schemas.master import (
    MasterInvite,
    MasterUpdate,
    MasterResponse,
    ScheduleUpdate,
    ScheduleExceptionCreate,
    ScheduleResponse,
)
from app.core.config import settings

router = APIRouter(tags=["Masters"])


# List masters
@router.get("/salons/{salon_id}/masters", response_model=List[MasterResponse])
async def get_salon_masters(
    salon_id: UUID,
    branch_id: Optional[UUID] = None,
    service_id: Optional[UUID] = None,
    is_active: bool = True,
    public: bool = False,
    db: Session = Depends(get_db),
):
    """Get list of masters for a salon"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    query = db.query(Master).filter(Master.salon_id == salon_id, Master.is_active == is_active)

    # Filter by branch if specified
    if branch_id:
        master_ids = (
            db.query(MasterBranch.master_id).filter(MasterBranch.branch_id == branch_id).all()
        )
        master_ids = [m[0] for m in master_ids]
        query = query.filter(Master.id.in_(master_ids))

    # Filter by service if specified
    if service_id:
        master_ids = (
            db.query(MasterService.master_id)
            .filter(MasterService.service_id == service_id, MasterService.is_active == True)
            .all()
        )
        master_ids = [m[0] for m in master_ids]
        query = query.filter(Master.id.in_(master_ids))

    masters = query.all()

    # Build response
    result = []
    for master in masters:
        user_data = {
            "id": str(master.user.id),
            "first_name": master.user.first_name,
            "last_name": master.user.last_name,
            "middle_name": master.user.middle_name,
            "photo_url": master.user.photo_url,
        }

        if not public:
            user_data["email"] = master.user.email

        result.append(
            {
                "id": master.id,
                "tier": master.tier.value,
                "specialization": master.specialization,
                "bio_ru": master.bio_ru,
                "experience_years": master.experience_years,
                "rating": master.rating,
                "total_reviews": master.total_reviews,
                "is_active": master.is_active,
                "user": user_data,
            }
        )

    return result


# Invite master
@router.post("/salons/{salon_id}/masters/invite", status_code=status.HTTP_201_CREATED)
async def invite_master(
    salon_id: UUID,
    invite_data: MasterInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Invite a new master to the salon"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Check permissions
    if salon.owner_id != current_user.id and current_user.role not in [
        UserRole.PLATFORM_ADMIN,
        UserRole.SALON_MANAGER,
    ]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Check if email already exists as a different role
    existing_user = db.query(User).filter(User.email == invite_data.email).first()
    if existing_user and existing_user.role not in [UserRole.MASTER, None]:
        raise HTTPException(status_code=400, detail="User already registered with different role")

    # Create user if doesn't exist
    if not existing_user:
        user = User(
            email=invite_data.email,
            first_name=invite_data.first_name,
            last_name=invite_data.last_name,
            middle_name=invite_data.middle_name,
            role=UserRole.MASTER,
            is_active=False,  # Will be activated when they accept
        )
        db.add(user)
        db.flush()
    else:
        user = existing_user

    # Create master record
    master = Master(
        user_id=user.id,
        salon_id=salon_id,
        tier=MasterTier[invite_data.tier.upper()],
        specialization=invite_data.specialization,
        invited_at=datetime.utcnow(),
        is_active=False,
        permissions={"can_manage_own_schedule": True, "can_edit_profile": True},
    )
    db.add(master)
    db.flush()

    # Associate with branches
    for branch_id in invite_data.branch_ids:
        branch = db.query(SalonBranch).filter(SalonBranch.id == branch_id).first()
        if branch and branch.salon_id == salon_id:
            master_branch = MasterBranch(master_id=master.id, branch_id=branch_id)
            db.add(master_branch)

    # Associate with services if provided
    if invite_data.service_ids:
        for service_id in invite_data.service_ids:
            service = db.query(Service).filter(Service.id == service_id).first()
            if service and service.salon_id == salon_id:
                master_service = MasterService(master_id=master.id, service_id=service_id)
                db.add(master_service)

    db.commit()

    # Send invitation email with token
    # Email service integration:
    # 1. Generate secure invitation token (JWT with expiration)
    # 2. Create invitation link: https://yourdomain.com/accept-invite?token={token}
    # 3. Send email via service (SendGrid, AWS SES, or local SMTP)
    #
    # Example implementation:
    # import jwt
    # from datetime import datetime, timedelta
    # invitation_token = jwt.encode({
    #     'master_id': str(master.id),
    #     'email': invite_data.email,
    #     'exp': datetime.utcnow() + timedelta(days=7)
    # }, settings.SECRET_KEY, algorithm='HS256')
    #
    # invitation_link = f"https://yourdomain.com/accept-invite?token={invitation_token}"
    #
    # from app.services.email import send_email
    # send_email(
    #     to=invite_data.email,
    #     subject=f"Invitation to join {salon.display_name}",
    #     body=f"You've been invited to join as a master. Click here: {invitation_link}"
    # )

    return {
        "id": str(master.id),
        "email": invite_data.email,
        "invited_at": master.invited_at,
        "message": "Master invited successfully. Email notification would be sent in production.",
    }


# Accept invitation
@router.post("/masters/accept-invitation/{token}")
async def accept_invitation(
    token: str,
    google_id_token: str,  # In real implementation, validate Google OAuth token
    db: Session = Depends(get_db),
):
    """Accept master invitation (simplified - full OAuth integration needed)"""
    # Google OAuth integration implementation guide:
    # 1. Verify and decode invitation token
    # 2. Validate Google ID token from frontend
    # 3. Extract user info from Google token
    # 4. Create or link user account
    # 5. Activate master profile
    #
    # Example implementation:
    # import jwt
    # from google.oauth2 import id_token
    # from google.auth.transport import requests
    #
    # # Verify invitation token
    # try:
    #     token_data = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    #     master_id = token_data['master_id']
    # except jwt.ExpiredSignatureError:
    #     raise HTTPException(status_code=400, detail="Invitation link expired")
    #
    # # Verify Google ID token
    # try:
    #     google_info = id_token.verify_oauth2_token(
    #         google_id_token,
    #         requests.Request(),
    #         settings.GOOGLE_CLIENT_ID
    #     )
    #     email = google_info['email']
    #     google_id = google_info['sub']
    # except ValueError:
    #     raise HTTPException(status_code=400, detail="Invalid Google token")
    #
    # # Get or create user
    # user = db.query(User).filter(User.email == email).first()
    # if not user:
    #     user = User(email=email, google_id=google_id, role=UserRole.MASTER)
    #     db.add(user)
    #     db.flush()
    #
    # # Update master profile
    # master = db.query(Master).filter(Master.id == master_id).first()
    # master.user_id = user.id
    # master.is_active = True
    # master.joined_at = datetime.utcnow()
    # db.commit()
    #
    # return {"message": "Invitation accepted successfully", "user_id": str(user.id)}

    raise HTTPException(
        status_code=501,
        detail="Full invitation acceptance requires Google OAuth integration. Use admin panel to manually activate masters for now.",
    )


# Update master
@router.patch("/salons/{salon_id}/masters/{master_id}", response_model=MasterResponse)
async def update_master(
    salon_id: UUID,
    master_id: UUID,
    master_update: MasterUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update master information"""
    master = db.query(Master).filter(Master.id == master_id, Master.salon_id == salon_id).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    salon = db.query(Salon).filter(Salon.id == salon_id).first()

    # Check permissions
    is_owner = salon.owner_id == current_user.id
    is_admin = current_user.role == UserRole.PLATFORM_ADMIN
    is_self = master.user_id == current_user.id
    can_edit_profile = master.permissions.get("can_edit_profile", False) if master.permissions else False

    if not (is_owner or is_admin or (is_self and can_edit_profile)):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Update fields
    if master_update.tier and (is_owner or is_admin):
        master.tier = MasterTier[master_update.tier.upper()]

    if master_update.specialization is not None:
        master.specialization = master_update.specialization

    if master_update.bio_ru is not None:
        master.bio_ru = master_update.bio_ru
    if master_update.bio_kk is not None:
        master.bio_kk = master_update.bio_kk
    if master_update.bio_en is not None:
        master.bio_en = master_update.bio_en

    if master_update.experience_years is not None:
        master.experience_years = master_update.experience_years

    if master_update.permissions and (is_owner or is_admin):
        master.permissions = master_update.permissions

    # Update branch associations if owner/admin
    if master_update.branch_ids and (is_owner or is_admin):
        # Remove existing
        db.query(MasterBranch).filter(MasterBranch.master_id == master_id).delete()
        # Add new
        for branch_id in master_update.branch_ids:
            master_branch = MasterBranch(master_id=master_id, branch_id=branch_id)
            db.add(master_branch)

    # Update service associations if owner/admin
    if master_update.service_ids and (is_owner or is_admin):
        # Remove existing
        db.query(MasterService).filter(MasterService.master_id == master_id).delete()
        # Add new
        for service_id in master_update.service_ids:
            master_service = MasterService(master_id=master_id, service_id=service_id)
            db.add(master_service)

    db.commit()
    db.refresh(master)

    return {
        "id": master.id,
        "tier": master.tier.value,
        "specialization": master.specialization,
        "bio_ru": master.bio_ru,
        "experience_years": master.experience_years,
        "rating": master.rating,
        "total_reviews": master.total_reviews,
        "is_active": master.is_active,
        "user": {
            "id": str(master.user.id),
            "first_name": master.user.first_name,
            "last_name": master.user.last_name,
            "email": master.user.email,
        },
    }


# Add portfolio images
@router.post("/salons/{salon_id}/masters/{master_id}/portfolio")
async def add_portfolio_images(
    salon_id: UUID,
    master_id: UUID,
    images: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add images to master's portfolio"""
    master = db.query(Master).filter(Master.id == master_id, Master.salon_id == salon_id).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    salon = db.query(Salon).filter(Salon.id == salon_id).first()

    # Check permissions
    is_owner = salon.owner_id == current_user.id
    is_self = master.user_id == current_user.id
    can_edit = master.permissions.get("can_edit_profile", False) if master.permissions else False

    if not (is_owner or (is_self and can_edit)):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Validate max 10 images
    if len(images) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed at once")

    # Save images
    os.makedirs("uploads/portfolio", exist_ok=True)
    uploaded_urls = []

    for image in images:
        # Validate file type
        if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            continue

        # Validate size
        contents = await image.read()
        if len(contents) > 5 * 1024 * 1024:
            continue

        # Save file
        file_extension = image.filename.split(".")[-1]
        filename = f"{uuid_lib.uuid4()}.{file_extension}"
        file_path = f"uploads/portfolio/{filename}"

        with open(file_path, "wb") as f:
            f.write(contents)

        uploaded_urls.append(f"/uploads/portfolio/{filename}")

    # Update master portfolio
    current_portfolio = master.portfolio_images or []
    master.portfolio_images = current_portfolio + uploaded_urls

    db.commit()

    return {"portfolio_images": master.portfolio_images}


# Delete portfolio image
@router.delete("/salons/{salon_id}/masters/{master_id}/portfolio", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_image(
    salon_id: UUID,
    master_id: UUID,
    image_url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete image from master's portfolio"""
    master = db.query(Master).filter(Master.id == master_id, Master.salon_id == salon_id).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    salon = db.query(Salon).filter(Salon.id == salon_id).first()

    # Check permissions
    is_owner = salon.owner_id == current_user.id
    is_self = master.user_id == current_user.id

    if not (is_owner or is_self):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Remove from portfolio
    if master.portfolio_images and image_url in master.portfolio_images:
        master.portfolio_images.remove(image_url)
        db.commit()

        # Delete file if local storage
        if image_url.startswith("/uploads/"):
            file_path = image_url.lstrip("/")
            if os.path.exists(file_path):
                os.remove(file_path)

    return None


# Deactivate master
@router.delete("/salons/{salon_id}/masters/{master_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_master(
    salon_id: UUID,
    master_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deactivate a master (soft delete)"""
    from app.models.booking import Booking, BookingStatus

    master = db.query(Master).filter(Master.id == master_id, Master.salon_id == salon_id).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    salon = db.query(Salon).filter(Salon.id == salon_id).first()

    # Check permissions (only owner can deactivate)
    if salon.owner_id != current_user.id and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Check for upcoming bookings
    upcoming_bookings = (
        db.query(Booking)
        .filter(
            Booking.master_id == master_id,
            Booking.booking_date >= datetime.utcnow().date(),
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        )
        .count()
    )

    if upcoming_bookings > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Master has {upcoming_bookings} upcoming bookings. Please cancel or reassign them first.",
        )

    # Deactivate
    master.is_active = False
    db.commit()

    return None


# Get master schedule
@router.get("/masters/{master_id}/schedule", response_model=ScheduleResponse)
async def get_master_schedule(
    master_id: UUID,
    branch_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
):
    """Get master's schedule"""
    master = db.query(Master).filter(Master.id == master_id).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    # Get regular schedule
    query = db.query(MasterSchedule).filter(MasterSchedule.master_id == master_id)

    if branch_id:
        query = query.filter(MasterSchedule.branch_id == branch_id)

    schedules = query.order_by(MasterSchedule.day_of_week).all()

    # Build regular schedule array (7 days)
    regular_schedule = []
    for day in range(1, 8):  # Monday (1) to Sunday (7)
        schedule = next((s for s in schedules if s.day_of_week == day), None)
        if schedule:
            regular_schedule.append(
                {
                    "day_of_week": day,
                    "is_working": schedule.is_working,
                    "start_time": str(schedule.start_time) if schedule.start_time else None,
                    "end_time": str(schedule.end_time) if schedule.end_time else None,
                    "breaks": schedule.breaks or [],
                }
            )
        else:
            regular_schedule.append({"day_of_week": day, "is_working": False})

    # Get future exceptions
    exceptions = (
        db.query(ScheduleException)
        .filter(
            ScheduleException.master_id == master_id,
            ScheduleException.exception_date >= datetime.utcnow().date(),
        )
        .order_by(ScheduleException.exception_date)
        .all()
    )

    exception_list = []
    for exc in exceptions:
        exception_list.append(
            {
                "id": str(exc.id),
                "exception_date": str(exc.exception_date),
                "exception_type": exc.exception_type.value,
                "custom_start_time": str(exc.custom_start_time) if exc.custom_start_time else None,
                "custom_end_time": str(exc.custom_end_time) if exc.custom_end_time else None,
                "reason": exc.reason,
            }
        )

    return {"regular_schedule": regular_schedule, "exceptions": exception_list}


# Update master schedule
@router.put("/masters/{master_id}/schedule", response_model=ScheduleResponse)
async def update_master_schedule(
    master_id: UUID,
    schedule_update: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update master's regular schedule"""
    master = db.query(Master).filter(Master.id == master_id).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    salon = db.query(Salon).filter(Salon.id == master.salon_id).first()

    # Check permissions
    is_owner = salon.owner_id == current_user.id
    is_self = master.user_id == current_user.id
    can_manage = master.permissions.get("can_manage_own_schedule", False) if master.permissions else False

    if not (is_owner or (is_self and can_manage)):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Validate branch
    branch = db.query(SalonBranch).filter(SalonBranch.id == schedule_update.branch_id).first()
    if not branch or branch.salon_id != master.salon_id:
        raise HTTPException(status_code=400, detail="Invalid branch")

    # Delete existing schedule for this branch
    db.query(MasterSchedule).filter(
        MasterSchedule.master_id == master_id, MasterSchedule.branch_id == schedule_update.branch_id
    ).delete()

    # Create new schedule
    for day_data in schedule_update.regular_schedule:
        schedule = MasterSchedule(
            master_id=master_id,
            branch_id=schedule_update.branch_id,
            day_of_week=day_data["day_of_week"],
            is_working=day_data.get("is_working", False),
            start_time=day_data.get("start_time"),
            end_time=day_data.get("end_time"),
            breaks=day_data.get("breaks", []),
        )
        db.add(schedule)

    db.commit()

    # Return updated schedule
    return await get_master_schedule(master_id, schedule_update.branch_id, db)


# Add schedule exception
@router.post("/masters/{master_id}/schedule/exceptions", status_code=status.HTTP_201_CREATED)
async def create_schedule_exception(
    master_id: UUID,
    exception_data: ScheduleExceptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add schedule exception"""
    master = db.query(Master).filter(Master.id == master_id).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    salon = db.query(Salon).filter(Salon.id == master.salon_id).first()

    # Check permissions
    is_owner = salon.owner_id == current_user.id
    is_self = master.user_id == current_user.id
    can_manage = master.permissions.get("can_manage_own_schedule", False) if master.permissions else False

    if not (is_owner or (is_self and can_manage)):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Validate date is in future
    if exception_data.exception_date < datetime.utcnow().date():
        raise HTTPException(status_code=400, detail="Exception date must be in the future")

    # Check for existing exception on this date
    existing = (
        db.query(ScheduleException)
        .filter(
            ScheduleException.master_id == master_id,
            ScheduleException.exception_date == exception_data.exception_date,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=409, detail="Exception already exists for this date")

    # Create exception
    exception = ScheduleException(
        master_id=master_id,
        exception_date=exception_data.exception_date,
        exception_type=ExceptionType[exception_data.exception_type.upper()],
        custom_start_time=exception_data.custom_start_time,
        custom_end_time=exception_data.custom_end_time,
        reason=exception_data.reason,
    )

    db.add(exception)
    db.commit()
    db.refresh(exception)

    return {
        "id": str(exception.id),
        "exception_date": str(exception.exception_date),
        "exception_type": exception.exception_type.value,
        "message": "Exception created successfully",
    }


# Delete schedule exception
@router.delete("/masters/{master_id}/schedule/exceptions/{exception_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule_exception(
    master_id: UUID,
    exception_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete schedule exception"""
    exception = (
        db.query(ScheduleException)
        .filter(ScheduleException.id == exception_id, ScheduleException.master_id == master_id)
        .first()
    )

    if not exception:
        raise HTTPException(status_code=404, detail="Exception not found")

    master = db.query(Master).filter(Master.id == master_id).first()
    salon = db.query(Salon).filter(Salon.id == master.salon_id).first()

    # Check permissions
    is_owner = salon.owner_id == current_user.id
    is_self = master.user_id == current_user.id

    if not (is_owner or is_self):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db.delete(exception)
    db.commit()

    return None
