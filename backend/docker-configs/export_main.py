"""
Production FastAPI Backend Template
===================================
Clean, production-ready FastAPI application for exported projects.
No sandbox-specific logic - runs identically whether from sandbox or locally.

Environment Variables:
- DATABASE_URL: Database connection string (default: sqlite:///./data/app.db)
- JWT_SECRET: Secret key for JWT token signing (REQUIRED in production)
- CORS_ORIGINS: Comma-separated list of allowed origins
- DEBUG: Enable debug mode (default: false)
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import JWTError, jwt
from passlib.context import CryptContext

# =============================================================================
# CONFIGURATION
# =============================================================================

class Settings:
    """Application settings from environment variables."""
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-this-in-production-use-strong-secret")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"
    ).split(",")

settings = Settings()

# =============================================================================
# DATABASE SETUP
# =============================================================================

# SQLite-specific: check_same_thread=False for async compatibility
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG
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
    price = Column(Float, default=0)
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
    password: str = Field(..., min_length=8)

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
    database: str
    timestamp: str

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
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
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
    """Application lifespan - create tables on startup."""
    # Ensure data directory exists
    import os
    os.makedirs("data", exist_ok=True)
    
    # Create all database tables
    Base.metadata.create_all(bind=engine)
    print(f"🚀 Application started")
    print(f"📦 Database: {settings.DATABASE_URL}")
    
    yield
    print("👋 Application shutting down")

app = FastAPI(
    title="API",
    description="Generated FastAPI Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# HEALTH ENDPOINT
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "database": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "API is running",
        "docs": "/docs",
        "health": "/health",
    }

# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post("/api/auth/signup", response_model=Token, tags=["Authentication"])
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if email already exists
    if db.query(UserModel).filter(UserModel.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username already exists
    if db.query(UserModel).filter(UserModel.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    user = UserModel(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        is_active=True,
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate token
    token = create_access_token({"sub": str(user.id)})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@app.post("/api/auth/login", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token."""
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is disabled")
    
    token = create_access_token({"sub": str(user.id)})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_me(current_user: UserModel = Depends(require_auth)):
    """Get current user profile."""
    return current_user

# =============================================================================
# ITEMS CRUD ENDPOINTS
# =============================================================================

@app.get("/api/items", response_model=List[ItemResponse], tags=["Items"])
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
    return items

@app.post("/api/items", response_model=ItemResponse, tags=["Items"])
async def create_item(
    item_data: ItemCreate,
    current_user: UserModel = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new item (requires authentication)."""
    item = ItemModel(
        name=item_data.name,
        description=item_data.description,
        price=item_data.price or 0,
        category=item_data.category,
        owner_id=current_user.id,
        is_active=True
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/api/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific item by ID."""
    item = db.query(ItemModel).filter(ItemModel.id == item_id, ItemModel.is_active == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/api/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def update_item(
    item_id: int,
    item_data: ItemUpdate,
    current_user: UserModel = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update an item (owner only)."""
    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this item")
    
    # Update fields
    if item_data.name is not None:
        item.name = item_data.name
    if item_data.description is not None:
        item.description = item_data.description
    if item_data.price is not None:
        item.price = item_data.price
    if item_data.category is not None:
        item.category = item_data.category
    
    db.commit()
    db.refresh(item)
    return item

@app.delete("/api/items/{item_id}", tags=["Items"])
async def delete_item(
    item_id: int,
    current_user: UserModel = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete an item (owner only, soft delete)."""
    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this item")
    
    item.is_active = False
    db.commit()
    
    return {"message": "Item deleted successfully"}

# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=settings.DEBUG
    )
