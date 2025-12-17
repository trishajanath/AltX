# Authentication Flow Diagram

## 🔐 Complete Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER REGISTRATION FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

1. User visits /auth
   │
   ├─→ [AuthPage.jsx]
   │   ├─ Email input
   │   ├─ Username input
   │   └─ Password input
   │
   └─→ Click "Create Account"
       │
       ├─→ [POST /api/auth/signup]
       │   │
       │   ├─→ [auth.py] validate_email(email)
       │   ├─→ [auth.py] validate_username(username)
       │   ├─→ [auth.py] validate_password(password)
       │   ├─→ [auth.py] hash_password(password) → bcrypt hash
       │   │
       │   └─→ [database.py] UserModel.create_user()
       │       │
       │       ├─→ Insert into MongoDB users collection
       │       │   {
       │       │     email: "user@example.com",
       │       │     username: "johndoe",
       │       │     hashed_password: "$2b$12$...",
       │       │     created_at: ISODate(...),
       │       │     is_active: true,
       │       │     is_verified: false
       │       │   }
       │       │
       │       └─→ Check unique constraints (email, username)
       │
       └─→ [auth.py] create_access_token(user_id)
           │
           ├─→ Generate JWT token
           │   {
           │     "sub": "507f1f77bcf86cd799439011",
           │     "exp": timestamp + 7 days
           │   }
           │
           └─→ Return response
               {
                 "success": true,
                 "access_token": "eyJhbGc...",
                 "token_type": "bearer",
                 "user": { id, email, username, ... }
               }
               │
               └─→ [AuthContext] login(user, token)
                   │
                   ├─→ Save to localStorage
                   │   - access_token
                   │   - user data
                   │
                   └─→ Navigate to /home ✅


┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER LOGIN FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

1. User visits /auth
   │
   ├─→ [AuthPage.jsx]
   │   ├─ Email input
   │   └─ Password input
   │
   └─→ Click "Login"
       │
       ├─→ [POST /api/auth/login]
       │   │
       │   ├─→ [database.py] UserModel.get_user_by_email(email)
       │   │   │
       │   │   └─→ Query MongoDB for user
       │   │       db.users.find_one({ email: "user@example.com" })
       │   │
       │   ├─→ [auth.py] verify_password(plain, hashed)
       │   │   │
       │   │   └─→ Bcrypt comparison
       │   │
       │   └─→ [auth.py] create_access_token(user_id)
       │
       └─→ Return response (same as signup)
           │
           └─→ [AuthContext] login(user, token)
               │
               └─→ Navigate to /home ✅


┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACCESSING PROTECTED ROUTE                            │
└─────────────────────────────────────────────────────────────────────────────┘

1. User tries to access /home
   │
   ├─→ [ProtectedRoute.jsx]
   │   │
   │   ├─→ Check [AuthContext]
   │   │   │
   │   │   ├─→ isAuthenticated?
   │   │   │   ├─ YES → Render children (HomePage)
   │   │   │   └─ NO  → Navigate to /auth
   │   │   │
   │   │   └─→ loading?
   │   │       └─ Show loading spinner
   │   │
   │   └─→ Render HomePage ✅


┌─────────────────────────────────────────────────────────────────────────────┐
│                      AUTHENTICATED API REQUEST FLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

1. Component makes API request
   │
   ├─→ [AuthContext] authenticatedFetch(url, options)
   │   │
   │   ├─→ Add headers
   │   │   {
   │   │     "Authorization": "Bearer eyJhbGc...",
   │   │     "Content-Type": "application/json"
   │   │   }
   │   │
   │   └─→ fetch(url, options)
   │
   └─→ [Backend Endpoint] @app.get("/api/protected")
       │
       ├─→ Depends(get_current_user)
       │   │
       │   ├─→ Extract token from Authorization header
       │   │
       │   ├─→ [auth.py] verify_token(token)
       │   │   │
       │   │   ├─→ Decode JWT
       │   │   ├─→ Verify signature
       │   │   ├─→ Check expiration
       │   │   │
       │   │   └─→ Extract user_id from "sub" claim
       │   │
       │   ├─→ [database.py] UserModel.get_user_by_id(user_id)
       │   │   │
       │   │   └─→ Query MongoDB
       │   │
       │   └─→ Check is_active
       │
       └─→ Return response with user data ✅


┌─────────────────────────────────────────────────────────────────────────────┐
│                             LOGOUT FLOW                                      │
└─────────────────────────────────────────────────────────────────────────────┘

1. User clicks "Logout"
   │
   ├─→ [AuthContext] logout()
   │   │
   │   ├─→ Clear state
   │   │   - setUser(null)
   │   │   - setToken(null)
   │   │
   │   └─→ Clear localStorage
   │       - removeItem('access_token')
   │       - removeItem('user')
   │
   └─→ Navigate to /auth ✅


┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOKEN EXPIRATION FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

1. API request with expired token
   │
   ├─→ [Backend] get_current_user()
   │   │
   │   ├─→ [auth.py] verify_token(token)
   │   │   │
   │   │   └─→ JWT decode fails (expired)
   │   │
   │   └─→ Raise HTTPException(401, "Invalid or expired token")
   │
   └─→ [Frontend] authenticatedFetch() catches 401
       │
       ├─→ [AuthContext] logout()
       │
       └─→ Throw error("Authentication expired. Please login again.")
           │
           └─→ User redirected to /auth


┌─────────────────────────────────────────────────────────────────────────────┐
│                           SECURITY FEATURES                                  │
└─────────────────────────────────────────────────────────────────────────────┘

Password Security:
├─ Bcrypt hashing (rounds=12)
├─ Automatic salt generation
├─ Never stored in plain text
└─ Never returned in API responses

JWT Security:
├─ HS256 algorithm (HMAC with SHA-256)
├─ 7-day expiration (configurable)
├─ Signed with SECRET_KEY
└─ Includes user_id in "sub" claim

Database Security:
├─ Unique indexes on email and username
├─ Email stored as lowercase
├─ No SQL injection (PyMongo parameterized queries)
└─ Connection string in .env (not committed)

API Security:
├─ HTTPBearer authentication scheme
├─ Token validation on every request
├─ Auto-logout on 401 errors
├─ CORS configuration
└─ Rate limiting (recommended to add)


┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW SUMMARY                                   │
└─────────────────────────────────────────────────────────────────────────────┘

Frontend Components:
  AuthPage.jsx ─────────┐
  ProtectedRoute.jsx ───┼─→ AuthContext ─→ localStorage
  UserProfile.jsx ──────┘                    ├─ access_token
                                              └─ user (JSON)

Backend Components:
  main.py ───┬─→ auth.py ──┬─→ password hashing (bcrypt)
             │              ├─→ JWT creation (python-jose)
             │              └─→ validation functions
             │
             └─→ database.py ─→ MongoDB
                                 └─ users collection


┌─────────────────────────────────────────────────────────────────────────────┐
│                       MONGODB COLLECTIONS                                    │
└─────────────────────────────────────────────────────────────────────────────┘

Database: altx_db

Collection: users
├─ Documents: User accounts
├─ Indexes:
│  ├─ _id (default, unique)
│  ├─ email (unique)
│  └─ username (unique)
│
└─ Schema:
   {
     _id: ObjectId,
     email: String,
     username: String,
     hashed_password: String,
     created_at: Date,
     updated_at: Date,
     is_active: Boolean,
     is_verified: Boolean
   }

Collection: projects (future)
├─ Documents: User projects
└─ Indexes:
   ├─ user_id
   └─ project_slug


┌─────────────────────────────────────────────────────────────────────────────┐
│                           DIRECTORY STRUCTURE                                │
└─────────────────────────────────────────────────────────────────────────────┘

AltX/
├── backend/
│   ├── database.py          ← MongoDB connection & UserModel
│   ├── auth.py              ← Password hashing & JWT
│   ├── main.py              ← Auth endpoints
│   ├── test_auth_system.py  ← Test script
│   └── .env                 ← MongoDB URL & JWT secret
│
└── frontend/
    └── src/
        ├── components/
        │   ├── AuthPage.jsx      ← Login/Signup UI
        │   ├── UserProfile.jsx   ← User info display
        │   └── ProtectedRoute.jsx ← Route guard
        ├── contexts/
        │   └── AuthContext.jsx   ← Global auth state
        └── App.jsx              ← AuthProvider wrapper
```
