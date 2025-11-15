from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import os
import uuid as uuid_lib
from slugify import slugify

from app.db.base import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.salon import Salon, SalonBranch, Service, SalonCategory, SubscriptionPlan
from app.schemas.salon import (
    SalonCreate,
    SalonUpdate,
    SalonResponse,
    BranchCreate,
    BranchResponse,
    ServiceCreate,
    ServiceResponse,
)
from datetime import date, timedelta

router = APIRouter(prefix="/salons", tags=["Salons"])


@router.post("", response_model=SalonResponse, status_code=status.HTTP_201_CREATED)
async def create_salon(
    salon_data: SalonCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Create new salon"""
    # Only allow users without existing salons or with proper permissions
    if current_user.role not in [UserRole.PLATFORM_ADMIN]:
        existing_salon = (
            db.query(Salon).filter(Salon.owner_id == current_user.id, Salon.deleted_at.is_(None)).first()
        )
        if existing_salon:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already owns a salon",
            )

    # Validate category exists
    category = db.query(SalonCategory).filter(SalonCategory.id == salon_data.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category ID")

    # Generate unique slug
    base_slug = slugify(salon_data.display_name)
    slug = base_slug
    counter = 1
    while db.query(Salon).filter(Salon.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Get trial subscription plan
    trial_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.plan_code == "trial").first()

    # Create salon
    salon = Salon(
        owner_id=current_user.id,
        category_id=salon_data.category_id,
        business_name=salon_data.business_name,
        display_name=salon_data.display_name,
        slug=slug,
        description_ru=salon_data.description_ru,
        description_kk=salon_data.description_kk,
        description_en=salon_data.description_en,
        email=salon_data.email,
        phone=salon_data.phone,
        website_url=salon_data.website_url,
        social_links=salon_data.social_links,
        subscription_plan_id=trial_plan.id if trial_plan else None,
        subscription_start_date=date.today(),
        subscription_end_date=date.today() + timedelta(days=14),
        is_active=True,
    )
    db.add(salon)
    db.flush()

    # Create main branch
    main_branch = SalonBranch(
        salon_id=salon.id,
        branch_name="Main Branch",
        display_name="Main Branch",
        city=salon_data.city,
        street_address="TBD",
        building_number="TBD",
        phone=salon_data.phone,
        email=salon_data.email,
        is_main=True,
        is_active=True,
    )
    db.add(main_branch)

    # Update user role if client
    if current_user.role == UserRole.CLIENT:
        current_user.role = UserRole.SALON_OWNER

    db.commit()
    db.refresh(salon)

    return salon


@router.get("/{salon_id}", response_model=SalonResponse)
async def get_salon(salon_id: UUID, db: Session = Depends(get_db)):
    """Get salon by ID"""
    salon = db.query(Salon).filter(Salon.id == salon_id, Salon.deleted_at.is_(None)).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    return salon


@router.patch("/{salon_id}", response_model=SalonResponse)
async def update_salon(
    salon_id: UUID,
    salon_update: SalonUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update salon information"""
    salon = db.query(Salon).filter(Salon.id == salon_id, Salon.deleted_at.is_(None)).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Check permissions
    if salon.owner_id != current_user.id and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Update fields
    if salon_update.display_name is not None:
        # Regenerate slug if display name changes
        base_slug = slugify(salon_update.display_name)
        slug = base_slug
        counter = 1
        while db.query(Salon).filter(Salon.slug == slug, Salon.id != salon_id).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        salon.slug = slug
        salon.display_name = salon_update.display_name

    if salon_update.description_ru is not None:
        salon.description_ru = salon_update.description_ru
    if salon_update.description_kk is not None:
        salon.description_kk = salon_update.description_kk
    if salon_update.description_en is not None:
        salon.description_en = salon_update.description_en
    if salon_update.phone is not None:
        salon.phone = salon_update.phone
    if salon_update.email is not None:
        salon.email = salon_update.email
    if salon_update.website_url is not None:
        salon.website_url = salon_update.website_url
    if salon_update.social_links is not None:
        salon.social_links = salon_update.social_links

    db.commit()
    db.refresh(salon)
    return salon


# Branches
@router.get("/{salon_id}/branches", response_model=List[BranchResponse])
async def get_salon_branches(salon_id: UUID, db: Session = Depends(get_db)):
    """Get all branches of a salon"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    branches = db.query(SalonBranch).filter(SalonBranch.salon_id == salon_id, SalonBranch.is_active == True).all()
    return branches


@router.post("/{salon_id}/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    salon_id: UUID,
    branch_data: BranchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create new branch for salon"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Check permissions
    if salon.owner_id != current_user.id and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Check subscription plan limits (TODO: implement based on plan features)

    branch = SalonBranch(
        salon_id=salon_id,
        branch_name=branch_data.branch_name,
        display_name=branch_data.display_name,
        city=branch_data.city,
        street_address=branch_data.street_address,
        building_number=branch_data.building_number,
        postal_code=branch_data.postal_code,
        phone=branch_data.phone,
        email=branch_data.email,
        latitude=branch_data.latitude,
        longitude=branch_data.longitude,
        working_hours=branch_data.working_hours,
        is_active=True,
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


# Services
@router.get("/{salon_id}/services", response_model=List[ServiceResponse])
async def get_salon_services(salon_id: UUID, db: Session = Depends(get_db)):
    """Get all services of a salon"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    services = db.query(Service).filter(Service.salon_id == salon_id, Service.is_active == True).all()
    return services


@router.post("/{salon_id}/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    salon_id: UUID,
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create new service for salon"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Check permissions
    if salon.owner_id != current_user.id and current_user.role not in [
        UserRole.PLATFORM_ADMIN,
        UserRole.SALON_MANAGER,
    ]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    service = Service(
        salon_id=salon_id,
        service_name_ru=service_data.service_name_ru,
        service_name_kk=service_data.service_name_kk,
        service_name_en=service_data.service_name_en,
        description_ru=service_data.description_ru,
        description_kk=service_data.description_kk,
        description_en=service_data.description_en,
        duration_minutes=service_data.duration_minutes,
        base_price=service_data.base_price,
        category=service_data.category,
        price_tiers=service_data.price_tiers,
        is_active=True,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service
