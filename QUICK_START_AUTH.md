# 🚀 Quick Start Guide - MongoDB Authentication

## ⚡ 3-Step Setup

### 1️⃣ Configure MongoDB (2 minutes)

**Get MongoDB Atlas (Free):**
```
1. Visit: https://www.mongodb.com/cloud/atlas/register
2. Create cluster (M0 Free tier)
3. Create database user
4. Get connection string
5. Whitelist IP: 0.0.0.0/0 (all IPs for development)
```

**Update backend/.env:**
```env
MONGODB_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/
MONGODB_DATABASE=altx_db
JWT_SECRET_KEY=run-python-c-import-secrets-print-secrets-token-urlsafe-32
```

### 2️⃣ Start Services (30 seconds)

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 3️⃣ Test It (1 minute)

**Visit:** http://localhost:5173/auth

**Create account:**
- Email: `test@example.com`
- Username: `testuser`
- Password: `TestPass123`

✅ **Done!** You're now logged in.

---

## 🎯 Key Endpoints

```
POST /api/auth/signup     - Create account
POST /api/auth/login      - Login
GET  /api/auth/me         - Get current user (requires token)
POST /api/auth/logout     - Logout
```

---

## 💻 Usage in Code

### Backend - Protect Endpoint
```python
from fastapi import Depends

@app.get("/api/protected")
async def protected(user: dict = Depends(get_current_user)):
    return {"user_id": user["_id"], "username": user["username"]}
```

### Frontend - Make Authenticated Request
```javascript
import { useAuth } from '../contexts/AuthContext';

function MyComponent() {
  const { authenticatedFetch, user } = useAuth();
  
  const getData = async () => {
    const res = await authenticatedFetch('http://localhost:8000/api/protected');
    const data = await res.json();
  };
  
  return <div>Hello {user.username}!</div>;
}
```

---

## 🔍 Test Everything

```bash
cd backend
python test_auth_system.py
```

---

## 🐛 Troubleshooting

**Can't connect?**
```bash
# Check backend is running:
curl http://localhost:8000/docs

# Check MongoDB connection:
# In backend/.env, verify MONGODB_URL is correct
```

**"Invalid token"?**
- Login again (tokens expire after 7 days)

**"Email already registered"?**
- Use different email or login with existing account

---

## 📚 Full Documentation

- **Complete Guide:** `MONGODB_AUTH_SETUP.md`
- **Implementation Summary:** `AUTH_IMPLEMENTATION_SUMMARY.md`

---

**🎉 That's it! You now have production-ready authentication!**
