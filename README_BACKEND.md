# Jazyl Platform Backend

Complete backend implementation for the Jazyl beauty salon platform following the technical specification.

## Features Implemented

### Core Functionality
- ✅ **Authentication System**
  - Phone verification via WhatsApp (simulation)
  - Google OAuth integration (prepared)
  - JWT token-based authentication

- ✅ **User Management**
  - User profiles with multiple roles (client, salon owner, manager, master, admin)
  - Profile updates and photo uploads

- ✅ **Salon Management**
  - Full CRUD operations for salons
  - Multi-branch support
  - Service catalog management
  - Automatic slug generation
  - Subscription plans (trial, basic, professional, enterprise)

- ✅ **Booking System**
  - Smart available slots calculation algorithm
  - Booking creation and management
  - Status workflow (pending → confirmed → in_progress → completed)
  - Conflict prevention

- ✅ **Review System**
  - Verified reviews (only after completed bookings)
  - Automatic rating calculations
  - Salon responses to reviews

- ✅ **Public Catalog**
  - Category-based browsing
  - Advanced search and filtering
  - Auction-based ranking algorithm
  - Promoted vs organic salon listings
  - Click tracking and budget management

### Database Schema
Complete PostgreSQL database schema with:
- Users and authentication
- Salons, branches, and services
- Masters, schedules, and exceptions
- Bookings and reviews
- Catalog impressions and clicks
- WhatsApp messaging integration
- Audit logging
- Payment tracking

## Project Structure

```
jazylll/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── users.py         # User management
│   │   │   ├── salons.py        # Salon CRUD operations
│   │   │   ├── bookings.py      # Booking system + slots algorithm
│   │   │   └── catalog.py       # Public catalog + ranking
│   │   └── deps.py              # Dependencies (auth, permissions)
│   ├── core/
│   │   ├── config.py            # Configuration settings
│   │   └── security.py          # JWT and security utilities
│   ├── db/
│   │   ├── base.py              # Database session
│   │   └── seed_data.py         # Initial data seeding
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py
│   │   ├── salon.py
│   │   ├── booking.py
│   │   ├── payment.py
│   │   ├── catalog.py
│   │   ├── communication.py
│   │   └── audit.py
│   ├── schemas/                 # Pydantic schemas
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── salon.py
│   │   ├── booking.py
│   │   └── catalog.py
│   └── main.py                  # FastAPI application
├── alembic/                     # Database migrations
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── run.py                       # Application entry point
```

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 15+
- Redis (optional, for token blacklisting)

### 2. Installation

```bash
# Clone the repository
cd jazylll

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required: DATABASE_URL, SECRET_KEY
```

### 4. Database Setup

```bash
# Create database
createdb jazyl

# Run migrations
alembic upgrade head

# Seed initial data (categories and plans)
python -m app.db.seed_data
```

### 5. Run Application

```bash
# Development mode with auto-reload
python run.py

# Or using uvicorn directly
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## Key API Endpoints

### Authentication
- `POST /api/v1/auth/request-code` - Request verification code
- `POST /api/v1/auth/verify-code` - Verify code and login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout

### Users
- `GET /api/v1/users/me` - Get current user
- `PATCH /api/v1/users/me` - Update profile
- `POST /api/v1/users/me/photo` - Upload photo

### Salons
- `POST /api/v1/salons` - Create salon
- `GET /api/v1/salons/{id}` - Get salon details
- `PATCH /api/v1/salons/{id}` - Update salon
- `GET /api/v1/salons/{id}/branches` - Get branches
- `POST /api/v1/salons/{id}/branches` - Create branch
- `GET /api/v1/salons/{id}/services` - Get services
- `POST /api/v1/salons/{id}/services` - Create service

### Bookings
- `GET /api/v1/bookings/masters/{master_id}/available-slots` - Get available slots
- `POST /api/v1/bookings` - Create booking
- `GET /api/v1/bookings` - List user bookings
- `GET /api/v1/bookings/{id}` - Get booking details
- `PATCH /api/v1/bookings/{id}` - Update booking status
- `POST /api/v1/bookings/reviews` - Create review

### Catalog
- `GET /api/v1/catalog/salons` - Browse salon catalog
- `POST /api/v1/catalog/salons/{id}/click` - Register click
- `GET /api/v1/catalog/salons/{slug}` - Get salon public page

## Algorithm Highlights

### Available Slots Calculation
The system calculates available booking slots by:
1. Checking master's regular schedule for the day
2. Applying schedule exceptions (days off, custom hours)
3. Retrieving existing bookings
4. Generating 15-minute interval slots
5. Filtering out:
   - Past time slots (< 1 hour from now)
   - Slots overlapping with breaks
   - Slots overlapping with existing bookings (+ 5min buffer)
6. Returning available slots that fit the service duration

### Catalog Ranking Algorithm
Salons are ranked using a hybrid approach:
1. **Promoted Salons**: Sorted by auction bid (descending)
2. **Organic Salons**: Composite scoring based on:
   - Rating (40% weight)
   - Review count (30% weight)
   - Recency/activity (30% weight)
3. **Interleaving**: 1 promoted : 3 organic ratio
4. **Cost Tracking**: Impressions and clicks logged with costs

## Database Models

### Key Tables
- `users` - All platform users (clients, staff, admins)
- `salon_categories` - 8 predefined business categories
- `salons` - Salon businesses
- `salon_branches` - Physical locations
- `services` - Services offered
- `masters` - Service providers
- `master_schedules` - Regular working hours
- `schedule_exceptions` - Special dates/hours
- `bookings` - Customer appointments
- `reviews` - Customer feedback
- `subscription_plans` - Pricing tiers
- `payments` - Financial transactions
- `catalog_impressions` - Catalog views
- `catalog_clicks` - User engagement

## Security Features

- JWT-based authentication with access/refresh tokens
- Password hashing (prepared for OAuth integration)
- Role-based access control
- Phone number verification
- SQL injection prevention (SQLAlchemy ORM)
- Input validation (Pydantic)
- CORS middleware

## Future Enhancements

To complete the full specification, consider:
- WhatsApp integration (using WhatsApp Business API or similar)
- Google OAuth completion (requires credentials)
- Master invitation flow
- Schedule management endpoints
- Payment gateway integration
- Site customization endpoints
- Admin panel endpoints
- Email notifications
- File upload to cloud storage (S3, etc.)
- Redis integration for token blacklisting
- Celery for background tasks
- Rate limiting
- Advanced analytics

## Development Notes

### Running Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest
```

## License

Proprietary - Jazyl Platform

## Support

For technical support or questions about the implementation, please refer to the original technical specification document (README.md).
