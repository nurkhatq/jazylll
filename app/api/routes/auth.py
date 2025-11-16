from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.schemas.auth import GoogleAuthRequest, TokenResponse
from app.models.user import User, UserRole
from app.core.security import create_access_token, create_refresh_token
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate with Google OAuth (id_token)

    1. Frontend sends Google id_token to this endpoint.
    2. Backend verifies token with Google.
    3. Finds or creates user in database.
    4. Returns JWT access & refresh tokens.
    """
    try:
        # 1️⃣ Verify token with Google
        idinfo = id_token.verify_oauth2_token(
            request.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=30
        )

        # 2️⃣ Extract user info
        google_id = idinfo['sub']
        email = idinfo.get('email')
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')

        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")

        # 3️⃣ Find or create user
        user = db.query(User).filter(
            (User.email == email) | (User.google_id == google_id)
        ).first()

        if not user:
            # Create new user (example: salon staff)
            user = User(
                email=email,
                google_id=google_id,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.SALON_OWNER,  # default role, adjust if needed
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update Google ID if missing
            if not user.google_id:
                user.google_id = google_id
                db.commit()

        # 4️⃣ Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Contact support.",
            )

        # 5️⃣ Optional: restrict login to certain roles
        if user.role == UserRole.CLIENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clients should use phone authentication",
            )

        # 6️⃣ Generate JWT tokens
        token_data = {
            "user_id": str(user.id),
            "role": user.role.value,
            "email": user.email,
        }
        access_token = create_access_token(token_data)
        refresh_token_str = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            user={
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
            },
        )

    except ValueError as e:
        # Token verification failed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}",
        )
    except ImportError:
        # Google auth library missing
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth requires 'google-auth' library. Install: pip install google-auth",
        )
