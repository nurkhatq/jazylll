from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.api.deps import get_current_user
from app.schemas.user import UserResponse, UserUpdate
from app.models.user import User
from app.models.booking import Booking, BookingStatus
import os
import uuid

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Update current user profile"""
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name
    if user_update.middle_name is not None:
        current_user.middle_name = user_update.middle_name
    if user_update.email is not None:
        # Check if email already exists
        existing = db.query(User).filter(User.email == user_update.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already exists")
        current_user.email = user_update.email

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/photo")
async def upload_user_photo(
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload user profile photo"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if photo.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG and PNG allowed")

    # Validate file size (5MB max)
    contents = await photo.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")

    # Save file
    os.makedirs("uploads/users", exist_ok=True)
    file_extension = photo.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"uploads/users/{filename}"

    with open(file_path, "wb") as f:
        f.write(contents)

    # Update user photo URL
    current_user.photo_url = f"/uploads/users/{filename}"
    db.commit()

    return {"photo_url": current_user.photo_url}
