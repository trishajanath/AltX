# main.py
# COMPLETE, PRODUCTION-READY FastAPI for web-comprehensive-website-346277

# --- Imports ---
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, Text,
                        ForeignKey, Enum as SQLAlchemyEnum)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.exc import IntegrityError
import enum

# --- Configuration ---
# In a real production environment, use environment variables (e.g., os.getenv)
# For this example, we'll define them here.
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_a_production_ready_app_346277")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
DATABASE_URL = "sqlite:///./psg_portal.db"

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Database Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Enums for Data Consistency ---
class UserRole(str, enum.Enum):
    STUDENT = "student"
    ALUMNI = "alumni"
    FACULTY = "faculty"
    PROSPECTIVE = "prospective" # For general registration
    ADMIN = "admin"

class DegreeLevel(str, enum.Enum):
    UG = "Undergraduate"
    PG = "Postgraduate"
    PHD = "PhD"

class ResourceType(str, enum.Enum):
    CALENDAR = "Academic Calendar"
    SCHEDULE = "Examination Schedule"
    CIRCULAR = "Official Circular"
    LINK = "Quick Link"
    FEE = "Fee Payment"

# --- SQLAlchemy Database Models ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.PROSPECTIVE, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    alumni_profile = relationship("AlumniProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    faculty_profile = relationship("FacultyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    department = Column(String, index=True, nullable=False)
    degree_level = Column(SQLAlchemyEnum(DegreeLevel), nullable=False)
    description = Column(Text, nullable=False)
    syllabus_url = Column(String)
    eligibility = Column(Text)

class CampusLocation(Base):
    __tablename__ = "campus_locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    tour_url = Column(String) # Link to the 360 view entry point
    hotspots = relationship("Hotspot", back_populates="location", cascade="all, delete-orphan")

class Hotspot(Base):
    __tablename__ = "hotspots"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("campus_locations.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    media_url = Column(String) # URL to an image or video
    location = relationship("CampusLocation", back_populates="hotspots")

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    resource_type = Column(SQLAlchemyEnum(ResourceType), nullable=False)
    url = Column(String, nullable=False) # File URL or external link
    published_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    graduation_year = Column(Integer)
    company = Column(String)
    job_title = Column(String)
    linkedin_profile = Column(String)
    is_spotlight = Column(Integer, default=0) # 0 for no, 1 for yes
    spotlight_story = Column(Text)
    user = relationship("User", back_populates="alumni_profile")

class NewsEvent(Base):
    __tablename__ = "news_events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    department = Column(String, index=True) # Can be "General" or a specific department
    event_date = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class FacultyProfile(Base):
    __tablename__ = "faculty_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    qualifications = Column(String)
    department = Column(String, index=True)
    research_interests = Column(Text)
    publications_link = Column(String)
    contact_email = Column(String)
    user = relationship("User", back_populates="faculty_profile")

# --- Pydantic Schemas (for API request/response validation) ---

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# User Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.PROSPECTIVE

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True

# Program Schemas
class ProgramResponse(BaseModel):
    id: int
    name: str
    department: str
    degree_level: DegreeLevel
    description: str
    syllabus_url: Optional[str] = None
    eligibility: Optional[str] = None

    class Config:
        from_attributes = True

# Virtual Tour Schemas
class HotspotResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    media_url: Optional[str] = None

    class Config:
        from_attributes = True

class CampusLocationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    tour_url: Optional[str] = None
    hotspots: List[HotspotResponse] = []

    class Config:
        from_attributes = True

# Resource Hub Schemas
class ResourceResponse(BaseModel):
    id: int
    title: str
    resource_type: ResourceType
    url: str
    published_date: datetime

    class Config:
        from_attributes = True

# Alumni Schemas
class AlumniProfileBase(BaseModel):
    graduation_year: Optional[int] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    linkedin_profile: Optional[str] = None

class AlumniProfileCreate(AlumniProfileBase):
    pass

class AlumniProfileResponse(AlumniProfileBase):
    user: UserResponse

    class Config:
        from_attributes = True

class AlumniSpotlightResponse(BaseModel):
    alumni_name: str
    graduation_year: Optional[int] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    spotlight_story: Optional[str] = None

# News & Events Schemas
class NewsEventResponse(BaseModel):
    id: int
    title: str
    content: str
    department: Optional[str] = None
    event_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Faculty Schemas
class FacultyProfileResponse(BaseModel):
    user_name: str
    user_email: EmailStr
    qualifications: Optional[str] = None
    department: Optional[str] = None
    research_interests: Optional[str] = None
    publications_link: Optional[str] = None
    contact_email: Optional[str] = None

    class Config:
        from_attributes = True

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Authentication Utilities ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Authentication Dependencies ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

# Role-based access dependencies
def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires '{required_role.value}' role."
            )
        return current_user
    return role_checker

# --- FastAPI Application Initialization ---
app = FastAPI(
    title="Educational Institution Portal API - PSG College of Technology",
    description="A comprehensive API for the PSG College of Technology portal, serving students, faculty, alumni, and prospective applicants.",
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@psgtech.edu",
    },
)

# --- Middleware ---

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"Request: {request.method} {request.url.path} | Response: {response.status_code} | Duration: {process_time:.4f}s"
    )
    return response

# --- Database Initialization on Startup ---
@app.on_event("startup")
def on_startup():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")

# --- API Endpoints ---

# Health Check
@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "app_name": "PSG College of Technology Portal API"}

# --- Authentication Router ---
auth_router = FastAPI()

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user. Default role is 'prospective'.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating user")
    return new_user

@auth_router.post("/login", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access and refresh tokens.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@auth_router.post("/refresh", response_model=Token, tags=["Authentication"])
async def refresh_access_token(current_user: User = Depends(get_current_user)):
    """
    Generate a new access token from a valid (non-expired) refresh token.
    Note: In this simplified setup, the refresh token is passed as a Bearer token.
    A more robust implementation would handle refresh tokens separately.
    """
    access_token = create_access_token(data={"sub": current_user.email})
    refresh_token = create_refresh_token(data={"sub": current_user.email}) # Optionally issue a new refresh token
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=UserResponse, tags=["Authentication"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get the profile of the currently authenticated user.
    """
    return current_user

app.include_router(auth_router, prefix="/api/v1/auth")

# --- Public Data Router (No Authentication Required) ---
public_router = FastAPI()

@public_router.get("/programs", response_model=List[ProgramResponse], tags=["Public Data"])
async def find_programs(
    department: Optional[str] = None,
    level: Optional[DegreeLevel] = None,
    db: Session = Depends(get_db)
):
    """
    Interactive Program Finder: Get a list of academic programs.
    Filter by `department` and/or `level` (UG, PG, PhD).
    """
    query = db.query(Program)
    if department:
        query = query.filter(Program.department.ilike(f"%{department}%"))
    if level:
        query = query.filter(Program.degree_level == level)
    return query.all()

@public_router.get("/campus-tour", response_model=List[CampusLocationResponse], tags=["Public Data"])
async def get_virtual_tour_locations(db: Session = Depends(get_db)):
    """
    Virtual Campus Tour: Get all main locations for the virtual tour.
    """
    return db.query(CampusLocation).all()

@public_router.get("/news-events", response_model=List[NewsEventResponse], tags=["Public Data"])
async def get_news_and_events(department: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Department-Specific News & Events Feed: Get all news and events.
    Filter by `department`.
    """
    query = db.query(NewsEvent).order_by(NewsEvent.created_at.desc())
    if department:
        query = query.filter(NewsEvent.department.ilike(f"%{department}%"))
    return query.all()

@public_router.get("/faculty", response_model=List[FacultyProfileResponse], tags=["Public Data"])
async def search_faculty_directory(
    query: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Searchable Faculty Directory: Search for faculty members.
    Search by `query` (name, research interests) and/or filter by `department`.
    """
    db_query = db.query(FacultyProfile).join(User)
    if department:
        db_query = db_query.filter(FacultyProfile.department.ilike(f"%{department}%"))
    if query:
        search_filter = (
            User.name.ilike(f"%{query}%") |
            FacultyProfile.research_interests.ilike(f"%{query}%")
        )
        db_query = db_query.filter(search_filter)
    
    results = db_query.all()
    # Manually construct response to include user details
    response = [
        FacultyProfileResponse(
            user_name=fp.user.name,
            user_email=fp.user.email,
            qualifications=fp.qualifications,
            department=fp.department,
            research_interests=fp.research_interests,
            publications_link=fp.publications_link,
            contact_email=fp.contact_email
        ) for fp in results
    ]
    return response

@public_router.get("/alumni/spotlight", response_model=List[AlumniSpotlightResponse], tags=["Public Data"])
async def get_alumni_spotlight(db: Session = Depends(get_db)):
    """
    Alumni Network & Success Stories: Get featured alumni success stories.
    """
    spotlight_profiles = db.query(AlumniProfile).filter(AlumniProfile.is_spotlight == 1).join(User).all()
    response = [
        AlumniSpotlightResponse(
            alumni_name=profile.user.name,
            graduation_year=profile.graduation_year,
            company=profile.company,
            job_title=profile.job_title,
            spotlight_story=profile.spotlight_story
        ) for profile in spotlight_profiles
    ]
    return response

app.include_router(public_router, prefix="/api/v1/public")

# --- Student Hub Router (Requires 'student' role) ---
student_router = FastAPI()

@student_router.get("/resources", response_model=List[ResourceResponse], tags=["Student Hub"])
async def get_student_resources(db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.STUDENT))):
    """
    Centralized Student Resource Hub: Get all essential academic resources.
    """
    return db.query(Resource).order_by(Resource.published_date.desc()).all()

app.include_router(student_router, prefix="/api/v1/student")

# --- Alumni Network Router (Requires 'alumni' role) ---
alumni_router = FastAPI()

@alumni_router.post("/profile", response_model=AlumniProfileResponse, tags=["Alumni Network"])
async def create_or_update_alumni_profile(
    profile_data: AlumniProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ALUMNI))
):
    """
    Create or update the profile for the currently logged-in alumnus.
    """
    profile = db.query(AlumniProfile).filter(AlumniProfile.user_id == current_user.id).first()
    if not profile:
        profile = AlumniProfile(user_id=current_user.id, **profile_data.model_dump())
        db.add(profile)
    else:
        for key, value in profile_data.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)
    
    db.commit()
    db.refresh(profile)
    return profile

@alumni_router.get("/profile/me", response_model=AlumniProfileResponse, tags=["Alumni Network"])
async def get_my_alumni_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ALUMNI))
):
    """
    Get the alumni profile of the currently logged-in user.
    """
    profile = db.query(AlumniProfile).filter(AlumniProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumni profile not found. Please create one.")
    return profile

app.include_router(alumni_router, prefix="/api/v1/alumni")

# --- Main execution for development ---
if __name__ == "__main__":
    import uvicorn
    print("--- Starting FastAPI server for PSG College of Technology Portal ---")
    print("API Docs available at http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)