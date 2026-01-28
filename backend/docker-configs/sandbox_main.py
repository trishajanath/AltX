"""
Sandbox FastAPI Backend Template
================================
Lightweight FastAPI application for AI-generated sandbox previews.
Runs fully isolated with SQLite and no external dependencies.

Environment Variables:
- SANDBOX: Set to 'true' for sandbox mode (uses SQLite)
- DATABASE_URL: Database connection string (default: sqlite:///./sandbox.db)
- JWT_SECRET: Secret key for JWT token signing
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import JWTError, jwt
from passlib.context import CryptContext

# =============================================================================
# CONFIGURATION - Read from environment variables
# =============================================================================

class Settings:
    """Application settings loaded from environment variables."""
    
    SANDBOX: bool = os.getenv("SANDBOX", "true").lower() == "true"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sandbox.db")
    
    # JWT Configuration - Use SANDBOX-ONLY secret in sandbox mode for isolation
    # This ensures sandbox tokens CANNOT work in production and vice versa
    _SANDBOX_JWT_SECRET: str = "sandbox-isolated-jwt-secret-do-not-use-in-production-" + os.getenv("SANDBOX_INSTANCE_ID", "default")
    _PRODUCTION_JWT_SECRET: str = os.getenv("JWT_SECRET", "production-secret-must-be-set")
    
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24 if not SANDBOX else 48  # Longer expiry for sandbox testing
    
    # Demo user configuration (sandbox only)
    DEMO_USER_EMAIL: str = "demo@sandbox.local"
    DEMO_USER_USERNAME: str = "demo_user"
    DEMO_USER_PASSWORD: str = "demo123456"  # Simple password for sandbox testing
    AUTO_CREATE_DEMO_USER: bool = os.getenv("AUTO_CREATE_DEMO_USER", "true").lower() == "true"
    
    # Email verification - DISABLED in sandbox mode
    REQUIRE_EMAIL_VERIFICATION: bool = not SANDBOX
    
    @classmethod
    def get_jwt_secret(cls) -> str:
        """Get the appropriate JWT secret based on environment.
        
        CRITICAL: Sandbox uses a completely different secret than production.
        This prevents sandbox tokens from being valid in production.
        """
        if cls.SANDBOX:
            return cls._SANDBOX_JWT_SECRET
        return cls._PRODUCTION_JWT_SECRET
    
    # Use SQLite for sandbox mode regardless of DATABASE_URL
    @classmethod
    def get_database_url(cls) -> str:
        if cls.SANDBOX:
            return "sqlite:///./data/sandbox.db"
        return cls.DATABASE_URL

settings = Settings()

# =============================================================================
# DATABASE SETUP - SQLite for sandbox, configurable for production
# =============================================================================

# SQLite-specific: check_same_thread=False for async compatibility
connect_args = {"check_same_thread": False} if "sqlite" in settings.get_database_url() else {}

engine = create_engine(
    settings.get_database_url(),
    connect_args=connect_args,
    echo=settings.SANDBOX  # Log SQL in sandbox mode
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# =============================================================================
# DATABASE MODELS
# =============================================================================

class UserModel(Base):
    """User database model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ItemModel(Base):
    """Generic item model for CRUD operations."""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, default=0)  # Store as cents
    category = Column(String(100), nullable=True)
    owner_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = 0
    category: Optional[str] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    category: Optional[str]
    owner_id: Optional[int]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    status: str
    sandbox: bool
    database: str
    timestamp: str
    auth_config: Optional[dict] = None


class DemoLoginRequest(BaseModel):
    """Request for quick demo login (sandbox only)."""
    pass


class DemoLoginResponse(BaseModel):
    """Response for demo login."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    message: str

# =============================================================================
# SECURITY UTILITIES
# =============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token using environment-appropriate secret."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "sandbox": settings.SANDBOX  # Mark token as sandbox/production
    })
    return jwt.encode(to_encode, settings.get_jwt_secret(), algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token.
    
    SECURITY: Only accepts tokens signed with the current environment's secret.
    Sandbox tokens cannot be used in production and vice versa.
    """
    try:
        payload = jwt.decode(token, settings.get_jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
        
        # Extra validation: ensure token sandbox flag matches current environment
        token_is_sandbox = payload.get("sandbox", False)
        if token_is_sandbox != settings.SANDBOX:
            print(f"⚠️ Token environment mismatch: token_sandbox={token_is_sandbox}, env_sandbox={settings.SANDBOX}")
            return None
        
        return payload
    except JWTError as e:
        print(f"⚠️ JWT decode error: {e}")
        return None

# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[UserModel]:
    """Get current authenticated user (returns None if not authenticated)."""
    if not token:
        return None
    
    payload = decode_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()
    return user

async def require_auth(
    current_user: Optional[UserModel] = Depends(get_current_user)
) -> UserModel:
    """Require authentication - raises 401 if not authenticated."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user

# =============================================================================
# APPLICATION SETUP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - create tables and demo user on startup."""
    # Create all database tables
    Base.metadata.create_all(bind=engine)
    print(f"🚀 Sandbox FastAPI started (SANDBOX={settings.SANDBOX})")
    print(f"📦 Database: {settings.get_database_url()}")
    print(f"🔐 JWT Secret Type: {'SANDBOX-ISOLATED' if settings.SANDBOX else 'PRODUCTION'}")
    print(f"📧 Email Verification: {'DISABLED' if not settings.REQUIRE_EMAIL_VERIFICATION else 'ENABLED'}")
    
    # Auto-create demo user in sandbox mode
    if settings.SANDBOX and settings.AUTO_CREATE_DEMO_USER:
        await _create_demo_user()
    
    yield
    print("👋 Sandbox FastAPI shutting down")


async def _create_demo_user():
    """Create a demo user for sandbox testing if it doesn't exist."""
    db = SessionLocal()
    try:
        # Check if demo user exists
        existing = db.query(UserModel).filter(UserModel.email == settings.DEMO_USER_EMAIL).first()
        if existing:
            print(f"✅ Demo user already exists: {settings.DEMO_USER_EMAIL}")
            return
        
        # Create demo user with is_verified=True (skip email verification)
        demo_user = UserModel(
            email=settings.DEMO_USER_EMAIL,
            username=settings.DEMO_USER_USERNAME,
            hashed_password=hash_password(settings.DEMO_USER_PASSWORD),
            is_active=True,
            is_verified=True  # Pre-verified for sandbox
        )
        db.add(demo_user)
        db.commit()
        
        print(f"🎉 Demo user created for sandbox testing:")
        print(f"   Email: {settings.DEMO_USER_EMAIL}")
        print(f"   Username: {settings.DEMO_USER_USERNAME}")
        print(f"   Password: {settings.DEMO_USER_PASSWORD}")
    except Exception as e:
        print(f"⚠️ Failed to create demo user: {e}")
        db.rollback()
    finally:
        db.close()

app = FastAPI(
    title="Sandbox API",
    description="AI-generated FastAPI backend for sandbox previews",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration for sandbox (allow all origins in sandbox mode)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.SANDBOX else ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# HEALTH ENDPOINT
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for container orchestration and monitoring.
    Returns the current status of the sandbox backend including auth config.
    """
    return {
        "status": "ok",
        "sandbox": settings.SANDBOX,
        "database": "sqlite" if "sqlite" in settings.get_database_url() else "postgresql",
        "timestamp": datetime.utcnow().isoformat(),
        "auth_config": {
            "email_verification_required": settings.REQUIRE_EMAIL_VERIFICATION,
            "demo_user_available": settings.SANDBOX and settings.AUTO_CREATE_DEMO_USER,
            "demo_email": settings.DEMO_USER_EMAIL if settings.SANDBOX else None,
            "jwt_type": "sandbox-isolated" if settings.SANDBOX else "production"
        }
    }

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Sandbox API is running",
        "docs": "/docs",
        "health": "/health",
        "sandbox_mode": settings.SANDBOX,
        "demo_login": "/api/auth/demo-login" if settings.SANDBOX else None
    }

# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post("/api/auth/demo-login", response_model=DemoLoginResponse, tags=["Authentication"])
async def demo_login(db: Session = Depends(get_db)):
    """Quick login with the pre-created demo user (SANDBOX MODE ONLY).
    
    This endpoint allows instant authentication without credentials,
    useful for testing and development. Only available in sandbox mode.
    
    Returns a valid JWT token for the demo user.
    """
    if not settings.SANDBOX:
        raise HTTPException(
            status_code=403, 
            detail="Demo login is only available in sandbox mode"
        )
    
    # Find demo user
    demo_user = db.query(UserModel).filter(UserModel.email == settings.DEMO_USER_EMAIL).first()
    
    if not demo_user:
        # Auto-create demo user if missing
        demo_user = UserModel(
            email=settings.DEMO_USER_EMAIL,
            username=settings.DEMO_USER_USERNAME,
            hashed_password=hash_password(settings.DEMO_USER_PASSWORD),
            is_active=True,
            is_verified=True
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        print(f"🎉 [SANDBOX] Demo user created on-demand: {demo_user.email}")
    
    # Generate token
    access_token = create_access_token(data={"sub": str(demo_user.id), "email": demo_user.email})
    
    print(f"🔓 [SANDBOX] Demo login successful for: {demo_user.email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": demo_user,
        "message": "Logged in as demo user. This is for testing purposes only."
    }


@app.post("/api/auth/signup", response_model=Token, tags=["Authentication"])
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account.
    
    In SANDBOX mode:
    - Email verification is DISABLED
    - Users are automatically verified upon signup
    - Simpler password requirements
    
    In PRODUCTION mode:
    - Email verification is REQUIRED
    - Users must verify email before full access
    - Strong password requirements enforced
    """
    # Check if email exists
    if db.query(UserModel).filter(UserModel.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username exists
    if db.query(UserModel).filter(UserModel.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Validate password (relaxed in sandbox, strict in production)
    if not settings.SANDBOX:
        if len(user_data.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        if not any(c.isupper() for c in user_data.password):
            raise HTTPException(status_code=400, detail="Password must contain uppercase letter")
        if not any(c.isdigit() for c in user_data.password):
            raise HTTPException(status_code=400, detail="Password must contain a number")
    
    # Create user - auto-verify in sandbox mode
    user = UserModel(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        is_verified=not settings.REQUIRE_EMAIL_VERIFICATION  # True in sandbox, False in production
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Log sandbox-specific behavior
    if settings.SANDBOX:
        print(f"📝 [SANDBOX] User registered (auto-verified): {user.email}")
    
    # Generate token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.post("/api/auth/login", response_model=Token, tags=["Authentication"])
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password.
    
    In SANDBOX mode:
    - Email verification check is SKIPPED
    - All registered users can login immediately
    
    In PRODUCTION mode:
    - Users must have verified email to login
    """
    user = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    # Check email verification (production only)
    if settings.REQUIRE_EMAIL_VERIFICATION and not user.is_verified:
        raise HTTPException(
            status_code=403, 
            detail="Please verify your email before logging in"
        )
    
    # Log sandbox-specific behavior
    if settings.SANDBOX:
        print(f"🔑 [SANDBOX] User logged in: {user.email}")
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@app.post("/api/auth/token", response_model=Token, tags=["Authentication"])
async def oauth2_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token endpoint (for Swagger UI and standard OAuth2 clients).
    
    Accepts username (email) and password via form data.
    """
    # OAuth2 spec uses 'username' field, but we use email
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401, 
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    if settings.REQUIRE_EMAIL_VERIFICATION and not user.is_verified:
        raise HTTPException(status_code=403, detail="Email verification required")
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@app.post("/api/auth/refresh", response_model=Token, tags=["Authentication"])
async def refresh_token(
    current_user: UserModel = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Refresh the current access token.
    
    Returns a new token with extended expiration.
    Requires a valid (non-expired) token.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    # Generate new token
    access_token = create_access_token(data={"sub": str(current_user.id), "email": current_user.email})
    
    if settings.SANDBOX:
        print(f"🔄 [SANDBOX] Token refreshed for: {current_user.email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": current_user
    }


@app.get("/api/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_me(current_user: UserModel = Depends(require_auth)):
    """Get current authenticated user's profile."""
    return current_user

@app.post("/api/auth/logout", tags=["Authentication"])
async def logout(current_user: UserModel = Depends(require_auth)):
    """Logout current user (client should discard token)."""
    if settings.SANDBOX:
        print(f"🚪 [SANDBOX] User logged out: {current_user.email}")
    return {"message": "Logged out successfully"}

# =============================================================================
# CRUD ENDPOINTS FOR GENERIC ITEMS
# =============================================================================

@app.get("/api/v1/items", response_model=List[ItemResponse], tags=["Items"])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all items with optional filtering."""
    query = db.query(ItemModel).filter(ItemModel.is_active == True)
    
    if category:
        query = query.filter(ItemModel.category == category)
    
    items = query.offset(skip).limit(limit).all()
    
    # Convert price from cents to dollars
    for item in items:
        item.price = item.price / 100 if item.price else 0
    
    return items

@app.post("/api/v1/items", response_model=ItemResponse, tags=["Items"])
async def create_item(
    item_data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user)
):
    """Create a new item."""
    item = ItemModel(
        name=item_data.name,
        description=item_data.description,
        price=int((item_data.price or 0) * 100),  # Store as cents
        category=item_data.category,
        owner_id=current_user.id if current_user else None
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    item.price = item.price / 100
    return item

@app.get("/api/v1/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific item by ID."""
    item = db.query(ItemModel).filter(ItemModel.id == item_id, ItemModel.is_active == True).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item.price = item.price / 100
    return item

@app.put("/api/v1/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def update_item(
    item_id: int,
    item_data: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_auth)
):
    """Update an existing item."""
    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update fields if provided
    if item_data.name is not None:
        item.name = item_data.name
    if item_data.description is not None:
        item.description = item_data.description
    if item_data.price is not None:
        item.price = int(item_data.price * 100)
    if item_data.category is not None:
        item.category = item_data.category
    
    db.commit()
    db.refresh(item)
    
    item.price = item.price / 100
    return item

@app.delete("/api/v1/items/{item_id}", tags=["Items"])
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_auth)
):
    """Delete an item (soft delete)."""
    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item.is_active = False
    db.commit()
    
    return {"message": "Item deleted successfully"}

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "sandbox_main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.SANDBOX
    )
