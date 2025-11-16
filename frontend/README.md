# Salon Booking Platform - Frontend

A comprehensive Next.js frontend for a salon booking platform with TypeScript and Tailwind CSS.

## Features

### Authentication
- **Google OAuth** - Sign in with Google for salon owners and managers
- **Phone Authentication** - SMS verification for clients
- **JWT Token Management** - Automatic token refresh and session handling
- **Role-based Access Control** - Different experiences for clients, salon owners, and admins

### Public Features
- **Homepage** - Browse salon categories with real-time data
- **Salon Catalog** - Filter by category, city, and search
- **Salon Details** - View services, masters, branches, and reviews
- **Booking System** - Complete flow with date/time slot selection

### Client Features
- **Profile Management** - View and edit account information
- **Bookings** - View, manage, and cancel appointments
- **Reviews** - Submit ratings and reviews after completed bookings

### Salon Owner Features
- **Multi-salon Dashboard** - Manage multiple salons from one account
- **Salon Editor** - Update business info, descriptions, contact details
- **Media Management** - Upload logo and cover photos
- **Branch Management** - Create and manage multiple locations
- **Master Management** - Invite masters, manage profiles and specializations
- **Service Management** - CRUD operations with multi-language support
- **Analytics** - View salon statistics and performance

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **OAuth**: @react-oauth/google
- **Icons**: Lucide React
- **Notifications**: React Hot Toast

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running at `http://localhost:8000`
- Google OAuth credentials (for Google sign-in)

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file:
```bash
cp .env.local.example .env.local
```

4. Configure environment variables in `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

### Running the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
frontend/
├── app/                          # Next.js app directory
│   ├── auth/
│   │   └── login/               # Login page with Google OAuth and phone auth
│   ├── catalog/                 # Public salon catalog
│   ├── dashboard/               # Salon owner dashboard
│   │   └── salons/
│   │       ├── create/          # Create new salon
│   │       └── [id]/
│   │           ├── edit/        # Edit salon settings
│   │           ├── masters/     # Manage masters
│   │           └── services/    # Manage services
│   ├── profile/                 # User profile
│   │   └── bookings/           # User bookings list
│   ├── salon/
│   │   └── [slug]/
│   │       ├── page.tsx        # Salon detail page
│   │       └── book/           # Booking flow
│   ├── layout.tsx              # Root layout with Google OAuth provider
│   └── page.tsx                # Homepage
├── components/
│   └── Navbar.tsx              # Navigation component
├── lib/
│   ├── api/                    # API client and service methods
│   │   ├── client.ts          # Axios instance with JWT interceptors
│   │   ├── auth.ts            # Authentication API
│   │   ├── categories.ts      # Categories API
│   │   ├── salons.ts          # Salons management API
│   │   └── bookings.ts        # Bookings and reviews API
│   └── store/
│       └── useAuthStore.ts    # Zustand auth state management
└── public/                     # Static assets
```

## API Integration

All API endpoints are integrated through the `/lib/api` layer:

- **Authentication**: `/auth/google`, `/auth/phone/send-code`, `/auth/phone/verify-code`
- **Categories**: `/categories` (public)
- **Catalog**: `/catalog/salons` (public)
- **Salons**: `/salons/*` (authenticated)
- **Masters**: `/masters/*` (authenticated)
- **Bookings**: `/bookings/*` (authenticated)
- **Reviews**: `/bookings/reviews` (mixed)

## Key Features Implementation

### Authentication Flow

1. User clicks "Sign in with Google"
2. Google OAuth popup opens
3. User authenticates with Google
4. Frontend receives `id_token`
5. Frontend sends `id_token` to backend `/auth/google`
6. Backend validates token and returns JWT tokens
7. Frontend stores tokens in Zustand + localStorage
8. Axios interceptor adds token to all requests
9. Auto-refresh on 401 errors

### Booking Flow

1. User browses salon catalog
2. Selects salon and views details
3. Chooses service, branch, and optionally a master
4. Clicks "Book Now" → redirects to booking page
5. Selects date from calendar
6. System fetches available time slots for selected master/date
7. User selects time slot
8. Reviews booking summary and adds notes
9. Confirms booking
10. Redirected to bookings list

### Salon Management Flow

1. Salon owner logs in with Google
2. Dashboard shows all owned salons
3. Can create new salon or edit existing
4. Upload logo and cover photos
5. Manage branches (locations)
6. Invite masters via email/phone
7. Create and manage services with pricing
8. View salon analytics and statistics

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | Yes |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth Client ID | Yes |

## Development Notes

- All data is fetched from real API endpoints (no mock data)
- Images are handled through backend file uploads
- Multi-language support (Russian, Kazakh, English) on services
- Responsive design works on mobile and desktop
- Real-time validation and error handling
- Toast notifications for user feedback

## Building for Production

```bash
npm run build
npm start
```

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript](https://www.typescriptlang.org/docs)
- [Zustand](https://github.com/pmndrs/zustand)
