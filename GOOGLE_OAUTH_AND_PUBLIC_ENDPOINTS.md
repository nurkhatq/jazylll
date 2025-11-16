# 🔐 Google OAuth & Public Endpoints Guide

## ✅ What I Just Added

### **New Public Endpoints (No Authentication Required):**

1. **GET /api/v1/categories** - List all salon categories
2. **GET /api/v1/categories/{category_id}** - Get single category
3. **GET /api/v1/categories/cities/list** - List cities with salons

These endpoints are **completely public** - anyone can access them without logging in!

---

## 📱 **How Google OAuth Works**

### **Important: Frontend + Backend Work Together**

Google OAuth is **NOT just backend** - it's a collaboration:

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │────────▶│    Google    │────────▶│   Backend   │
│   (React)   │         │    OAuth     │         │  (FastAPI)  │
└─────────────┘         └──────────────┘         └─────────────┘
```

### **Step-by-Step Flow:**

#### **1. Frontend Setup** (Your React/Vue/Next.js App)

```bash
# Install Google OAuth library
npm install @react-oauth/google
```

```javascript
// In your App.js or main component
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

function App() {
  const handleGoogleSuccess = async (credentialResponse) => {
    // credentialResponse.credential is the id_token
    const response = await fetch('http://localhost:8000/api/v1/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id_token: credentialResponse.credential
      })
    });

    const data = await response.json();
    // data contains: access_token, refresh_token, user info

    // Save tokens to localStorage
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    console.log('Logged in as:', data.user);
  };

  return (
    <GoogleOAuthProvider clientId="YOUR_GOOGLE_CLIENT_ID">
      <div>
        <h1>Login to Jazyl</h1>
        <GoogleLogin
          onSuccess={handleGoogleSuccess}
          onError={() => console.log('Login Failed')}
        />
      </div>
    </GoogleOAuthProvider>
  );
}
```

#### **2. Backend Receives Token** (Already Implemented!)

The backend:
1. ✅ Receives `id_token` from frontend
2. ✅ Validates token with Google servers
3. ✅ Extracts user info (email, name, google_id)
4. ✅ Creates or finds user in database
5. ✅ Returns JWT access & refresh tokens

**Backend Code Location:** `app/api/routes/auth.py` - Line 138

---

## 🔧 **Setup Instructions**

### **Step 1: Get Google OAuth Credentials**

1. **Go to Google Cloud Console:**
   ```
   https://console.cloud.google.com/
   ```

2. **Create Project:**
   - Click "Select a project" → "New Project"
   - Name: "Jazyl Platform"
   - Click "Create"

3. **Enable Google+ API:**
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

4. **Configure OAuth Consent Screen:**
   - Go to "APIs & Services" → "OAuth consent screen"
   - User Type: **External**
   - App name: **Jazyl Platform**
   - Support email: your email
   - Add scopes: `email`, `profile`
   - Save and continue

5. **Create OAuth Client ID:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: **Web application**
   - Name: "Jazyl Web Client"

   **Authorized JavaScript origins:**
   ```
   http://localhost:3000
   http://localhost:8000
   https://yourdomain.com
   ```

   **Authorized redirect URIs:**
   ```
   http://localhost:3000
   http://localhost:8000/api/v1/auth/google/callback
   https://yourdomain.com/auth/callback
   ```

6. **Copy Credentials:**
   You'll receive:
   - **Client ID:** `123456789-abcdefg.apps.googleusercontent.com`
   - **Client Secret:** `GOCSPX-abcdefg123456`

### **Step 2: Update Backend .env**

```bash
# Create .env if it doesn't exist
cp .env.example .env

# Edit .env and add:
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefg123456
```

### **Step 3: Install Backend Dependencies**

```bash
pip install google-auth google-auth-oauthlib
# OR (already in requirements.txt)
pip install -r requirements.txt
```

### **Step 4: Frontend Setup**

**For React:**
```bash
npm install @react-oauth/google
```

**For Vue:**
```bash
npm install vue3-google-login
```

**For Next.js:**
```bash
npm install @react-oauth/google
```

---

## 📋 **Complete Public Endpoints List**

### **Categories (NEW! ✨)**

#### **GET /api/v1/categories**
Get all salon categories with salon counts

**Example:**
```bash
curl http://localhost:8000/api/v1/categories
```

**Response:**
```json
[
  {
    "id": "uuid-here",
    "code": "hair_salon",
    "name_ru": "Парикмахерская",
    "name_kk": "Шаштараз",
    "name_en": "Hair Salon",
    "description_ru": "Услуги стрижки и укладки",
    "icon_url": "/icons/hair.svg",
    "salon_count": 45
  },
  {
    "id": "uuid-here",
    "code": "nail_salon",
    "name_ru": "Маникюр и педикюр",
    "name_kk": "Маникюр және педикюр",
    "name_en": "Nail Salon",
    "icon_url": "/icons/nails.svg",
    "salon_count": 32
  }
]
```

#### **GET /api/v1/categories/{category_id}**
Get single category details

#### **GET /api/v1/categories/cities/list**
Get cities that have salons

**Example:**
```bash
curl "http://localhost:8000/api/v1/categories/cities/list?category_id=uuid-here"
```

**Response:**
```json
[
  { "city": "Almaty", "salon_count": 125 },
  { "city": "Astana", "salon_count": 87 },
  { "city": "Shymkent", "salon_count": 43 }
]
```

---

### **Catalog (Already Existed)**

#### **GET /api/v1/catalog/salons**
Browse salons by category

**Parameters:**
- `category_id` (required) - Category UUID
- `city` (optional) - Filter by city
- `search` (optional) - Search query
- `sort` (optional) - relevance | rating | recent
- `page` (optional) - Page number (default: 1)
- `per_page` (optional) - Items per page (default: 20)

**Example:**
```bash
curl "http://localhost:8000/api/v1/catalog/salons?category_id=uuid&city=Almaty&page=1"
```

#### **GET /api/v1/catalog/salons/{salon_slug}**
Get public salon page

**Example:**
```bash
curl http://localhost:8000/api/v1/catalog/salons/beauty-studio-almaty
```

---

## 🎯 **Frontend Implementation Examples**

### **Example 1: Homepage - Show Categories**

```javascript
// React component
import { useState, useEffect } from 'react';

function Categories() {
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/categories')
      .then(res => res.json())
      .then(data => setCategories(data));
  }, []);

  return (
    <div className="categories-grid">
      {categories.map(category => (
        <div key={category.id} className="category-card">
          <img src={category.icon_url} alt={category.name_en} />
          <h3>{category.name_en}</h3>
          <p>{category.salon_count} salons</p>
          <a href={`/catalog?category=${category.id}`}>View Salons</a>
        </div>
      ))}
    </div>
  );
}
```

### **Example 2: Salon Catalog Page**

```javascript
function SalonCatalog() {
  const [salons, setSalons] = useState([]);
  const [cities, setCities] = useState([]);
  const categoryId = new URLSearchParams(window.location.search).get('category');

  useEffect(() => {
    // Load cities for filter
    fetch(`http://localhost:8000/api/v1/categories/cities/list?category_id=${categoryId}`)
      .then(res => res.json())
      .then(data => setCities(data));

    // Load salons
    fetch(`http://localhost:8000/api/v1/catalog/salons?category_id=${categoryId}`)
      .then(res => res.json())
      .then(data => setSalons(data.items));
  }, [categoryId]);

  return (
    <div>
      <h1>Salons</h1>

      {/* City filter */}
      <select onChange={e => filterByCity(e.target.value)}>
        <option value="">All Cities</option>
        {cities.map(city => (
          <option key={city.city} value={city.city}>
            {city.city} ({city.salon_count})
          </option>
        ))}
      </select>

      {/* Salon list */}
      {salons.map(salon => (
        <div key={salon.id} className="salon-card">
          <img src={salon.cover_image_url} alt={salon.display_name} />
          <h3>{salon.display_name}</h3>
          <p>⭐ {salon.rating} ({salon.total_reviews} reviews)</p>
          <p>📍 {salon.city}</p>
          <a href={`/salon/${salon.slug}`}>View Details</a>
        </div>
      ))}
    </div>
  );
}
```

### **Example 3: Google Login for Salon Owners**

```javascript
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

function SalonOwnerLogin() {
  const handleLogin = async (credentialResponse) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: credentialResponse.credential })
      });

      const data = await response.json();

      if (response.ok) {
        // Save tokens
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);

        // Redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        alert('Login failed: ' + data.detail);
      }
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  return (
    <GoogleOAuthProvider clientId="YOUR_GOOGLE_CLIENT_ID">
      <div className="login-page">
        <h1>Salon Owner Login</h1>
        <p>Sign in with your Google account</p>
        <GoogleLogin
          onSuccess={handleLogin}
          onError={() => alert('Login failed')}
          text="signin_with"
          shape="rectangular"
          theme="filled_blue"
        />
      </div>
    </GoogleOAuthProvider>
  );
}
```

---

## 🔑 **Using Authenticated Endpoints**

After login, use the access token for protected endpoints:

```javascript
// Store token after login
localStorage.setItem('access_token', 'your-jwt-token-here');

// Use it in subsequent requests
async function getMyProfile() {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/api/v1/users/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const profile = await response.json();
  console.log(profile);
}

// Create a salon
async function createSalon(salonData) {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/api/v1/salons', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(salonData)
  });

  return await response.json();
}
```

---

## 🚀 **Quick Testing**

### **Test Public Endpoints (No Auth):**

```bash
# Get all categories
curl http://localhost:8000/api/v1/categories

# Get cities
curl http://localhost:8000/api/v1/categories/cities/list

# Browse catalog (replace uuid with actual category ID)
curl "http://localhost:8000/api/v1/catalog/salons?category_id=your-category-uuid"
```

### **Test Google OAuth:**

1. Start backend: `python run.py`
2. Visit Swagger UI: `http://localhost:8000/api/v1/docs`
3. Find `/auth/google` endpoint
4. Click "Try it out"
5. You'll need an `id_token` from Google (get it from frontend first)

---

## 📦 **Complete Authentication Options**

Your platform supports **2 authentication methods:**

### **1. Phone Authentication (For Clients)**
```javascript
// Step 1: Request code
await fetch('/api/v1/auth/request-code', {
  method: 'POST',
  body: JSON.stringify({ phone: '+77012345678' })
});

// Step 2: Verify code
const response = await fetch('/api/v1/auth/verify-code', {
  method: 'POST',
  body: JSON.stringify({ phone: '+77012345678', code: '123456' })
});

const { access_token } = await response.json();
```

### **2. Google OAuth (For Salon Staff)**
```javascript
// Frontend gets id_token from Google
// Then sends to backend
const response = await fetch('/api/v1/auth/google', {
  method: 'POST',
  body: JSON.stringify({ id_token: googleCredential })
});
```

---

## ✅ **Summary**

### **What You Have Now:**

✅ **Public Endpoints:**
- Categories listing
- Cities listing
- Salon catalog
- Salon public pages

✅ **Google OAuth:**
- Full implementation in backend
- Detailed frontend examples
- Step-by-step setup guide

✅ **Ready to Use:**
- All public data accessible without login
- OAuth flow documented with code examples
- Both authentication methods working

### **What You Need to Do:**

1. ✅ Get Google OAuth credentials (5 minutes)
2. ✅ Update `.env` file
3. ✅ Implement frontend with examples above
4. ✅ Test everything!

---

## 🎊 **You're All Set!**

Your backend is **completely ready** for frontend integration. All public endpoints work immediately, and Google OAuth just needs credentials to be configured.

**Any questions? Check the code comments in:**
- `app/api/routes/auth.py` (OAuth implementation)
- `app/api/routes/categories.py` (Public endpoints)

**Happy coding! 🚀**
