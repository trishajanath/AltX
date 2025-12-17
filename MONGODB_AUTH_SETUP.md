# MongoDB Authentication System - Setup Guide

## ✅ Implementation Complete

A complete MongoDB-based authentication system has been implemented with JWT tokens, password hashing, and a beautiful React UI.

---

## 📁 Files Created

### Backend Files

1. **`backend/database.py`**
   - MongoDB connection manager (singleton pattern)
   - UserModel class with CRUD operations
   - Automatic index creation for email/username uniqueness

2. **`backend/auth.py`**
   - Password hashing with bcrypt
   - JWT token creation and verification
   - Email, password, and username validation
   - Security: 8+ chars, uppercase, lowercase, number required

3. **`backend/main.py`** (Updated)
   - Added authentication imports
   - Security middleware (HTTPBearer)
   - 4 new endpoints:
     - `POST /api/auth/signup` - Register new account
     - `POST /api/auth/login` - Login with email/password
     - `GET /api/auth/me` - Get current user info
     - `POST /api/auth/logout` - Logout (client-side token removal)
   - Authentication helpers:
     - `get_current_user()` - Required auth dependency
     - `get_current_user_optional()` - Optional auth dependency

### Frontend Files

1. **`frontend/src/components/AuthPage.jsx`**
   - Beautiful animated login/signup page
   - Framer Motion animations
   - Email, username, password fields
   - Real-time error/success messages
   - Toggle between login and signup modes

2. **`frontend/src/contexts/AuthContext.jsx`**
   - Global authentication state management
   - Auto-load user from localStorage
   - `authenticatedFetch()` helper with auto-retry
   - Login/logout functions
   - Token management

3. **`frontend/src/components/ProtectedRoute.jsx`** (Updated)
   - Uses AuthContext for authentication
   - Loading state during auth check
   - Auto-redirect to `/auth` if not logged in

4. **`frontend/src/App.jsx`** (Updated)
   - Wrapped with AuthProvider
   - Added `/auth` route for login/signup

---

## 🔧 Configuration Required

### 1. MongoDB Setup

You need to set up a MongoDB database. Choose one option:

#### Option A: MongoDB Atlas (Recommended - Free Cloud Database)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Create a free account and cluster
3. Get your connection string (looks like):
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. Update `backend/.env`:
   ```env
   MONGODB_URL=mongodb+srv://your-username:your-password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DATABASE=altx_db
   ```

#### Option B: Local MongoDB

1. Install MongoDB locally
2. Start MongoDB service
3. Update `backend/.env`:
   ```env
   MONGODB_URL=mongodb://localhost:27017/
   MONGODB_DATABASE=altx_db
   ```

### 2. JWT Secret Key

Generate a secure random secret key:

```bash
# Windows PowerShell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update `backend/.env`:
```env
JWT_SECRET_KEY=your-generated-secret-key-here
```

---

## 🚀 Usage

### Start Backend
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Access the App
- Navigate to `http://localhost:5173/auth`
- Create an account or login
- Protected routes will now require authentication

---

## 🔐 API Endpoints

### Public Endpoints (No Auth Required)

#### Sign Up
```http
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "username": "johndoe",
    "is_verified": false,
    "created_at": "2025-11-15T10:30:00"
  }
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** (Same as signup)

### Protected Endpoints (Require Auth Token)

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "username": "johndoe",
    "is_verified": false,
    "is_active": true,
    "created_at": "2025-11-15T10:30:00",
    "updated_at": "2025-11-15T10:30:00"
  }
}
```

#### Logout
```http
POST /api/auth/logout
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 🛡️ Security Features

### Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number

### Username Requirements
- 3-30 characters
- Must start with a letter
- Only letters, numbers, underscores, and hyphens

### Email Validation
- Standard email format validation
- Stored as lowercase

### Password Security
- Hashed with bcrypt (automatic salt)
- Never stored in plain text
- Never returned in API responses

### JWT Tokens
- Signed with HS256 algorithm
- 7-day expiration (configurable)
- Includes user ID in payload
- Auto-refresh on API calls

---

## 🎨 Frontend Features

### AuthPage Component
- **Animated gradient background** with floating orbs
- **Smooth transitions** between login/signup modes
- **Real-time validation** feedback
- **Password visibility toggle**
- **Loading states** during API calls
- **Error/success messages** with animations
- **Responsive design** for all screen sizes

### AuthContext
- **Global state management** for authentication
- **Automatic token persistence** in localStorage
- **Auto-redirect** on token expiration
- **Helper functions** for authenticated API calls

### ProtectedRoute
- **Loading spinner** while checking auth
- **Auto-redirect** to `/auth` if not logged in
- **Seamless integration** with React Router

---

## 📊 Database Schema

### Users Collection

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "email": "user@example.com",          // Unique index
  "username": "johndoe",                 // Unique index
  "hashed_password": "$2b$12$...",      // Bcrypt hash
  "created_at": ISODate("2025-11-15"),
  "updated_at": ISODate("2025-11-15"),
  "is_active": true,
  "is_verified": false
}
```

### Indexes
- `email` (unique)
- `username` (unique)
- `user_id` (for projects collection)

---

## 🔄 Using Authentication in Your Code

### Backend - Protect an Endpoint

```python
from fastapi import Depends

@app.get("/api/my-protected-endpoint")
async def protected_endpoint(current_user: dict = Depends(get_current_user)):
    """
    This endpoint requires authentication.
    current_user will contain the authenticated user's data.
    """
    return {
        "message": f"Hello {current_user['username']}!",
        "user_id": current_user["_id"]
    }
```

### Backend - Optional Authentication

```python
@app.get("/api/my-optional-auth-endpoint")
async def optional_auth(user: dict = Depends(get_current_user_optional)):
    """
    This endpoint works with or without authentication.
    user will be None if not authenticated.
    """
    if user:
        return {"message": f"Hello {user['username']}!"}
    else:
        return {"message": "Hello anonymous user!"}
```

### Frontend - Make Authenticated Requests

```javascript
import { useAuth } from '../contexts/AuthContext';

function MyComponent() {
  const { authenticatedFetch, user } = useAuth();

  const fetchData = async () => {
    try {
      const response = await authenticatedFetch('http://localhost:8000/api/my-data');
      const data = await response.json();
      console.log(data);
    } catch (error) {
      console.error('Failed:', error);
    }
  };

  return (
    <div>
      <h1>Welcome {user?.username}!</h1>
      <button onClick={fetchData}>Fetch Data</button>
    </div>
  );
}
```

---

## 🐛 Troubleshooting

### "Connection failed" error
- Check if backend is running on port 8000
- Verify MongoDB connection string in `.env`
- Check MongoDB Atlas IP whitelist (allow 0.0.0.0/0 for development)

### "Email already registered" error
- Email is already in use
- Check MongoDB to verify or use different email

### "Invalid token" error
- Token expired (7 days)
- Token was manually deleted from localStorage
- JWT secret changed in `.env`
- Solution: Login again

### ProtectedRoute redirects immediately
- Check browser console for errors
- Verify token exists in localStorage: `localStorage.getItem('access_token')`
- Check if AuthProvider wraps your app in App.jsx

---

## 📝 Next Steps (Optional Enhancements)

1. **Email Verification**
   - Send verification emails on signup
   - Verify email before allowing full access

2. **Password Reset**
   - "Forgot password" flow
   - Email with reset token

3. **OAuth Integration**
   - Google/GitHub login
   - Social authentication

4. **User Profiles**
   - Profile pictures
   - Bio and additional fields
   - Profile update endpoints

5. **Role-Based Access Control**
   - Admin/user roles
   - Permission system
   - Role-based routes

6. **Session Management**
   - Active sessions tracking
   - Logout from all devices
   - Session history

---

## ✅ Testing

### Test Signup
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPass123"
  }'
```

### Test Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123"
  }'
```

### Test Protected Endpoint
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

---

## 🎉 Summary

Your authentication system is now complete with:
- ✅ MongoDB database integration
- ✅ Secure password hashing (bcrypt)
- ✅ JWT token authentication
- ✅ Beautiful React UI with animations
- ✅ Global auth state management
- ✅ Protected routes
- ✅ Input validation
- ✅ Error handling
- ✅ Auto-redirect for unauthorized users

Just configure your MongoDB connection string and JWT secret, then you're ready to go! 🚀
