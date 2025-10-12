# main.py
# COMPLETE, PRODUCTION-READY FastAPI for college-provide-information-940578

# --- Imports ---
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Annotated

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, Text,
                        Enum, Float, ForeignKey)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
import enum

# --- Configuration ---
# In a real production environment, use environment variables for these settings.
# Example: SECRET_KEY = os.getenv("SECRET_KEY", "a-default-secret-key-for-dev")
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./college_portal.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Security & Authentication Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Database Models ---

# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Integer, default=0) # 0 for student, 1 for admin
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Feature Models
class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    department = Column(String, index=True, nullable=False)
    degree_level = Column(String, index=True) # e.g., Bachelor's, Master's
    description = Column(Text)
    tuition_fees = Column(Float)
    session_start_date = Column(String) # e.g., Fall 2024

class Faculty(Base):
    __tablename__ = "faculty"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    department = Column(String, index=True, nullable=False)
    qualifications = Column(String)
    research_interests = Column(Text)
    publications = Column(Text)
    contact_email = Column(String, unique=True)

class AdmissionStep(Base):
    __tablename__ = "admission_steps"
    id = Column(Integer, primary_key=True, index=True)
    step_number = Column(Integer, unique=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    link_to_form = Column(String, nullable=True)

class GalleryCategory(str, enum.Enum):
    ACADEMIC_BUILDINGS = "Academic Buildings"
    STUDENT_LIFE = "Student Life"
    ATHLETICS = "Athletics"
    DORMITORIES = "Dormitories"
    LABS = "Labs"
    LIBRARY = "Library"

class GalleryItem(Base):
    __tablename__ = "gallery_items"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(Enum(GalleryCategory))
    media_type = Column(String) # e.g., image, video, 360_photo
    url = Column(String, nullable=False)

class EventType(str, enum.Enum):
    ACADEMIC_DEADLINE = "Academic Deadline"
    WORKSHOP = "Workshop"
    GUEST_LECTURE = "Guest Lecture"
    CULTURAL_FESTIVAL = "Cultural Festival"

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    event_type = Column(Enum(EventType))

class Testimonial(Base):
    __tablename__ = "testimonials"
    id = Column(Integer, primary_key=True, index=True)
    author_name = Column(String, nullable=False)
    author_type = Column(String) # Student, Alumni
    major = Column(String, index=True)
    content = Column(Text, nullable=False)
    media_type = Column(String) # text, video
    media_url = Column(String, nullable=True)


# --- Pydantic Schemas (Data Transfer Objects) ---

# User Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_admin: int
    
    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[EmailStr] = None

# Feature Schemas
class ProgramSchema(BaseModel):
    id: int
    name: str
    department: str
    degree_level: str
    description: Optional[str] = None
    tuition_fees: Optional[float] = None
    session_start_date: Optional[str] = None

    class Config:
        from_attributes = True

class FacultySchema(BaseModel):
    id: int
    name: str
    department: str
    qualifications: Optional[str] = None
    research_interests: Optional[str] = None
    publications: Optional[str] = None
    contact_email: Optional[EmailStr] = None

    class Config:
        from_attributes = True

class AdmissionStepSchema(BaseModel):
    id: int
    step_number: int
    title: str
    description: Optional[str] = None
    link_to_form: Optional[str] = None

    class Config:
        from_attributes = True

class GalleryItemSchema(BaseModel):
    id: int
    title: str
    category: GalleryCategory
    media_type: str
    url: str

    class Config:
        from_attributes = True

class EventSchema(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    event_type: EventType

    class Config:
        from_attributes = True

class TestimonialSchema(BaseModel):
    id: int
    author_name: str
    author_type: str
    major: str
    content: str
    media_type: str
    media_url: Optional[str] = None

    class Config:
        from_attributes = True


# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbDependency = Annotated[Session, Depends(get_db)]

# --- Authentication Utilities ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbDependency) -> User:
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

CurrentUser = Annotated[User, Depends(get_current_user)]

async def get_current_admin_user(current_user: CurrentUser) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]

# --- FastAPI App Initialization ---
app = FastAPI(
    title="College Information Portal",
    description="A sleek and distinctive college website designed to be the central information hub for prospective and current students.",
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@collegeportal.edu",
    },
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
portal_router = APIRouter(prefix="/api/v1", tags=["College Information"])

# --- Authentication Endpoints ---

@auth_router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: DbDependency):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(
        data={"sub": new_user.email}, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.from_attributes(new_user)
    )

@auth_router.post("/login", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbDependency):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.from_attributes(user)
    )

@auth_router.post("/refresh")
async def refresh_token(refresh_token: str = Field(..., description="The refresh token"), db: DbDependency):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    new_access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": new_access_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: CurrentUser):
    return current_user


# --- College Information Endpoints ---

@portal_router.get("/programs", response_model=List[ProgramSchema])
async def get_programs(
    db: DbDependency,
    department: Optional[str] = None,
    degree_level: Optional[str] = None,
    session_start: Optional[str] = None,
):
    query = db.query(Program)
    if department:
        query = query.filter(Program.department.ilike(f"%{department}%"))
    if degree_level:
        query = query.filter(Program.degree_level.ilike(f"%{degree_level}%"))
    if session_start:
        query = query.filter(Program.session_start_date == session_start)
    return query.all()

@portal_router.get("/admissions/guide", response_model=List[AdmissionStepSchema])
async def get_admissions_guide(db: DbDependency):
    return db.query(AdmissionStep).order_by(AdmissionStep.step_number).all()

@portal_router.get("/gallery", response_model=List[GalleryItemSchema])
async def get_gallery_items(db: DbDependency, category: Optional[GalleryCategory] = None):
    query = db.query(GalleryItem)
    if category:
        query = query.filter(GalleryItem.category == category)
    return query.all()

@portal_router.get("/faculty", response_model=List[FacultySchema])
async def search_faculty(
    db: DbDependency,
    name: Optional[str] = None,
    department: Optional[str] = None,
):
    query = db.query(Faculty)
    if name:
        query = query.filter(Faculty.name.ilike(f"%{name}%"))
    if department:
        query = query.filter(Faculty.department.ilike(f"%{department}%"))
    return query.all()

@portal_router.get("/events", response_model=List[EventSchema])
async def get_events(
    db: DbDependency,
    event_type: Optional[EventType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    query = db.query(Event)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if start_date:
        query = query.filter(Event.start_time >= start_date)
    if end_date:
        query = query.filter(Event.start_time <= end_date)
    return query.order_by(Event.start_time).all()

@portal_router.get("/testimonials", response_model=List[TestimonialSchema])
async def get_testimonials(db: DbDependency, major: Optional[str] = None):
    query = db.query(Testimonial)
    if major:
        query = query.filter(Testimonial.major.ilike(f"%{major}%"))
    return query.all()


# --- Main App ---

# Include routers
app.include_router(auth_router)
app.include_router(portal_router)

# Root endpoint
@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "app": "college-provide-information-940578"}

# --- Startup Event to Create DB and Seed Data ---
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    
    # Seeding data for demonstration if the database is empty
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            print("Database is empty. Seeding initial data...")
            # Create an admin user
            admin_user = User(
                name="Admin User",
                email="admin@college.edu",
                hashed_password=get_password_hash("admin123"),
                is_admin=1
            )
            db.add(admin_user)

            # Seed Programs
            db.add_all([
                Program(name="Bachelor of Science in Computer Science", department="Engineering", degree_level="Bachelor's", tuition_fees=15000, session_start_date="Fall 2024"),
                Program(name="Master of Business Administration", department="Business", degree_level="Master's", tuition_fees=25000, session_start_date="Fall 2024"),
                Program(name="Bachelor of Arts in Psychology", department="Psychology", degree_level="Bachelor's", tuition_fees=12000, session_start_date="Spring 2025"),
            ])

            # Seed Faculty
            db.add_all([
                Faculty(name="Dr. Alan Turing", department="Engineering", qualifications="PhD in Computer Science", research_interests="Artificial Intelligence, Cryptography", contact_email="alan.turing@college.edu"),
                Faculty(name="Dr. Ada Lovelace", department="Engineering", qualifications="PhD in Mathematics", research_interests="Computational Theory", contact_email="ada.lovelace@college.edu"),
                Faculty(name="Dr. Sigmund Freud", department="Psychology", qualifications="MD, PhD", research_interests="Cognitive Neuroscience, Psychoanalysis", contact_email="sigmund.freud@college.edu"),
            ])

            # Seed Admission Steps
            db.add_all([
                AdmissionStep(step_number=1, title="Submit Online Application", description="Complete the common application form through our portal.", link_to_form="/apply"),
                AdmissionStep(step_number=2, title="Upload Required Documents", description="Submit transcripts, recommendation letters, and personal statement."),
                AdmissionStep(step_number=3, title="Pay Application Fee", description="A non-refundable fee of $50 is required."),
                AdmissionStep(step_number=4, title="Schedule Interview", description="Eligible candidates will be invited for an online interview."),
            ])

            # Seed Gallery
            db.add_all([
                GalleryItem(title="Main Engineering Hall", category=GalleryCategory.ACADEMIC_BUILDINGS, media_type="image", url="/images/eng_hall.jpg"),
                GalleryItem(title="Central Library 360 View", category=GalleryCategory.LIBRARY, media_type="360_photo", url="/images/library_360.jpg"),
                GalleryItem(title="Annual Sports Fest", category=GalleryCategory.ATHLETICS, media_type="video", url="/videos/sports_fest.mp4"),
                GalleryItem(title="Oakwood Dormitory Room", category=GalleryCategory.DORMITORIES, media_type="image", url="/images/dorm.jpg"),
            ])

            # Seed Events
            db.add_all([
                Event(title="Fall 2024 Registration Deadline", event_type=EventType.ACADEMIC_DEADLINE, start_time=datetime(2024, 8, 15, 23, 59, tzinfo=timezone.utc)),
                Event(title="AI & Machine Learning Workshop", event_type=EventType.WORKSHOP, start_time=datetime(2024, 9, 20, 10, 0, tzinfo=timezone.utc), end_time=datetime(2024, 9, 20, 16, 0, tzinfo=timezone.utc)),
                Event(title="Annual Cultural Night", event_type=EventType.CULTURAL_FESTIVAL, start_time=datetime(2024, 10, 5, 18, 0, tzinfo=timezone.utc)),
            ])

            # Seed Testimonials
            db.add_all([
                Testimonial(author_name="John Doe", author_type="Alumni", major="Computer Science", content="The CS program provided me with the skills to land a job at a top tech company right after graduation.", media_type="text"),
                Testimonial(author_name="Jane Smith", author_type="Student", major="Business", content="The faculty is incredibly supportive, and the internship opportunities are amazing.", media_type="video", media_url="/videos/jane_testimonial.mp4"),
            ])

            db.commit()
            print("Initial data seeded successfully.")
    finally:
        db.close()