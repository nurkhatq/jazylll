"""
Jazyl Platform - Main Application Entry Point

Comprehensive beauty salon management platform with enhanced security,
role-based access control, and audit logging.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.redis_client import redis_client
from app.core.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    AuditLogMiddleware,
    RequestValidationMiddleware
)
from app.api.routes import (
    auth,
    users,
    salons,
    bookings,
    salon_bookings,  # NEW: Salon booking management
    catalog,
    masters,
    advertising,
    sites,
    admin,
    categories
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    print("🚀 Starting Jazyl Platform...")
    print(f"📋 Environment: {settings.ENVIRONMENT}")
    print(f"🔒 Debug Mode: {settings.DEBUG}")

    # Initialize Redis connection
    redis_client.connect()

    # Validate critical configurations
    if not settings.SECRET_KEY:
        print("⚠️  WARNING: SECRET_KEY not configured properly!")

    if settings.ENVIRONMENT == "production":
        if not settings.GOOGLE_CLIENT_ID:
            print("⚠️  WARNING: GOOGLE_CLIENT_ID not set")
        if not settings.WHATSAPP_API_KEY:
            print("⚠️  WARNING: WHATSAPP_API_KEY not set")

    print("✅ Jazyl Platform started successfully!")

    yield  # Application runs

    # Shutdown
    print("👋 Shutting down Jazyl Platform...")
    redis_client.close()
    print("✅ Cleanup completed")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="""
    **Jazyl Platform** - Comprehensive Beauty Salon Management System

    ## Features
    * 🔐 Secure authentication with Google OAuth & WhatsApp phone verification
    * 👥 Role-based access control (RBAC)
    * 📊 Comprehensive audit logging
    * 🔒 JWT token management with blacklist
    * 🚦 Rate limiting for API protection
    * 📱 WhatsApp integration for notifications
    * 🏪 Multi-tenant salon management
    * 📅 Smart booking system
    * ⭐ Review and rating system
    * 📈 Analytics and reporting

    ## Security
    * Token rotation for refresh tokens
    * IP-based rate limiting
    * Comprehensive audit trail
    * Role-based permissions
    * Session management
    """,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# =========================================
# MIDDLEWARE CONFIGURATION (Order matters!)
# =========================================

# 1. Security Headers (first to apply to all responses)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Request Validation (before processing)
app.add_middleware(RequestValidationMiddleware)

# 3. Rate Limiting (before expensive operations)
app.add_middleware(RateLimitMiddleware)

# 4. Audit Logging (after rate limiting, before business logic)
app.add_middleware(AuditLogMiddleware)

# 5. CORS (last, to handle preflight requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# =========================================
# DIRECTORY SETUP
# =========================================

# Create upload directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/users", exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/salons", exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/services", exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/masters", exist_ok=True)

# Mount static files
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# =========================================
# API ROUTES
# =========================================

# Authentication (public)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["Authentication"])

# Public endpoints
app.include_router(categories.router, prefix=settings.API_V1_PREFIX, tags=["Categories"])
app.include_router(catalog.router, prefix=settings.API_V1_PREFIX, tags=["Public Catalog"])

# Protected endpoints
app.include_router(users.router, prefix=settings.API_V1_PREFIX, tags=["Users"])
app.include_router(salons.router, prefix=settings.API_V1_PREFIX, tags=["Salons"])
app.include_router(masters.router, prefix=settings.API_V1_PREFIX, tags=["Masters"])
app.include_router(bookings.router, prefix=settings.API_V1_PREFIX, tags=["Bookings"])
app.include_router(salon_bookings.router, prefix=settings.API_V1_PREFIX, tags=["Salon Booking Management"])
app.include_router(advertising.router, prefix=settings.API_V1_PREFIX, tags=["Advertising"])
app.include_router(sites.router, prefix=settings.API_V1_PREFIX, tags=["Site Customization"])

# Admin endpoints
app.include_router(admin.router, prefix=settings.API_V1_PREFIX, tags=["Admin"])


# =========================================
# ROOT ENDPOINTS
# =========================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": "Welcome to Jazyl Platform API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "health": "/health",
        "features": {
            "authentication": ["Google OAuth", "WhatsApp Phone Verification"],
            "security": ["JWT Tokens", "Rate Limiting", "Audit Logging", "RBAC"],
            "integrations": ["WhatsApp", "Google OAuth"]
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint - System status
    """
    redis_status = "connected" if redis_client.is_connected() else "disconnected"

    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "services": {
            "api": "operational",
            "redis": redis_status,
        }
    }


# =========================================
# MAIN ENTRY POINT
# =========================================

if __name__ == "__main__":
    import uvicorn

    print(f"""
    ╔═══════════════════════════════════════╗
    ║     JAZYL PLATFORM - STARTING         ║
    ║                                       ║
    ║  Environment: {settings.ENVIRONMENT:24} ║
    ║  Debug: {str(settings.DEBUG):30} ║
    ╚═══════════════════════════════════════╝
    """)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
