import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Annotated

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, Text, 
                        Boolean, ForeignKey, Enum as SQLAlchemyEnum, Float)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.exc import IntegrityError
import enum

# --- Configuration ---
# In a real production app, these should come from environment variables or a config file.
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_development_only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
DATABASE_URL = "sqlite:///./inclusive_college.db"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 Scheme ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Database Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbDep = Annotated[Session, Depends(get_db)]

# --- Enums for Roles and Categories ---
class UserRole(str, enum.Enum):
    student = "student"
    faculty = "faculty"
    staff = "staff"

class EventCategory(str, enum.Enum):
    academic = "Academic"
    queer_student_union = "Queer Student Union"
    disability_services = "Disability Services"
    faculty_resources = "Faculty Resources"
    dei_training = "DEI Training"
    social = "Social"
    club_meeting = "Club Meeting"

class ResourceCategory(str, enum.Enum):
    all_gender_restroom = "All-Gender Restroom"
    mental_health = "Mental Health"
    accessibility = "Accessibility Services"
    mutual_aid = "Mutual Aid"
    study_space = "Study Space"
    other = "Other"

# --- SQLAlchemy Models ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    chosen_name = Column(String, index=True)
    pronouns = Column(String)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    enrollments = relationship("Enrollment", back_populates="student")
    taught_courses = relationship("Course", back_populates="faculty")
    rsvps = relationship("RSVP", back_populates="user")
    photos = relationship("GalleryPhoto", back_populates="uploader")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    course_code = Column(String, unique=True, index=True, nullable=False)
    syllabus = Column(Text)
    faculty_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    faculty = relationship("User", back_populates="taught_courses")
    enrollments = relationship("Enrollment", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(String) # e.g., "A", "B+", "In Progress"

    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String)
    category = Column(SQLAlchemyEnum(EventCategory), nullable=False)

    # Relationships
    rsvps = relationship("RSVP", back_populates="event", cascade="all, delete-orphan")

class RSVP(Base):
    __tablename__ = "rsvps"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="rsvps")
    event = relationship("Event", back_populates="rsvps")

class GalleryPhoto(Base):
    __tablename__ = "gallery_photos"
    id = Column(Integer, primary_key=True, index=True)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_url = Column(String, nullable=False)
    caption = Column(String)
    event_tag = Column(String)
    academic_year = Column(String)
    consent_given = Column(Boolean, default=False, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    uploader = relationship("User", back_populates="photos")

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    category = Column(SQLAlchemyEnum(ResourceCategory), nullable=False)
    location = Column(String)
    contact_info = Column(String)
    tags = Column(String) # Comma-separated tags like "wheelchair accessible"

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# --- Pydantic Schemas (for API input/output validation) ---

# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    chosen_name: Optional[str] = None
    pronouns: Optional[str] = None
    role: UserRole

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    chosen_name: Optional[str] = None
    pronouns: Optional[str] = None
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# Dashboard Schemas
class StudentCourseInfo(BaseModel):
    course_id: int
    course_code: str
    title: str
    grade: Optional[str] = None

    class Config:
        from_attributes = True

class StudentDashboard(BaseModel):
    user_info: UserResponse
    courses: List[StudentCourseInfo]
    financial_aid_status: str = "In Good Standing" # Placeholder

class FacultyCourseInfo(BaseModel):
    course_id: int
    course_code: str
    title: str
    roster_count: int

class FacultyDashboard(BaseModel):
    user_info: UserResponse
    teaching_courses: List[FacultyCourseInfo]

# Event Schemas
class EventCreate(BaseModel):
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str
    category: EventCategory

class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str
    category: EventCategory
    rsvp_count: int

    class Config:
        from_attributes = True

# Gallery Schemas
class PhotoUpload(BaseModel):
    image_url: str
    caption: Optional[str] = None
    event_tag: Optional[str] = None
    academic_year: Optional[str] = None
    consent_given: bool

class PhotoResponse(BaseModel):
    id: int
    uploader: UserResponse
    image_url: str
    caption: Optional[str] = None
    event_tag: Optional[str] = None
    academic_year: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Resource Schemas
class ResourceCreate(BaseModel):
    name: str
    description: str
    category: ResourceCategory
    location: Optional[str] = None
    contact_info: Optional[str] = None
    tags: Optional[str] = None

class ResourceResponse(BaseModel):
    id: int
    name: str
    description: str
    category: ResourceCategory
    location: Optional[str] = None
    contact_info: Optional[str] = None
    tags: Optional[str] = None

    class Config:
        from_attributes = True

# Feedback Schema
class FeedbackCreate(BaseModel):
    content: str

# Course Schemas
class RosterMember(BaseModel):
    student_id: int
    full_name: str
    chosen_name: Optional[str] = None
    pronouns: Optional[str] = None

class CourseDetailResponse(BaseModel):
    id: int
    title: str
    course_code: str
    syllabus: Optional[str] = None
    faculty: UserResponse
    roster: List[RosterMember]

    class Config:
        from_attributes = True

# --- Authentication and Security Utilities ---

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
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(data, expires_delta=expires)

def get_user(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbDep) -> User:
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
    
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

# --- FastAPI Application Instance ---
app = FastAPI(
    title="Inclusive College Community Platform",
    description="A comprehensive web portal for a genderqueer and all-inclusive college.",
    version="1.0.0",
)

# --- Middleware ---

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"method={request.method} path={request.url.path} status={response.status_code} duration={process_time:.4f}s"
    )
    return response

# --- Event Handlers ---
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")

# --- API Endpoints ---

# Health Check
@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "app_name": "Inclusive College Community Platform"}

# --- Authentication API Router ---
auth_router = FastAPI()

@auth_router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: DbDep):
    db_user = get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        chosen_name=user.chosen_name or user.full_name,
        pronouns=user.pronouns,
        role=user.role
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": new_user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@auth_router.post("/login", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbDep):
    user = get_user(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@auth_router.post("/refresh", response_model=Token)
async def refresh_access_token(current_user: CurrentUser):
    new_access_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = create_refresh_token(data={"sub": current_user.email})
    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: CurrentUser):
    return current_user

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

# --- Dashboard API ---
@app.get("/api/v1/dashboard", response_model=StudentDashboard | FacultyDashboard, tags=["Dashboard"])
async def get_dashboard(current_user: CurrentUser, db: DbDep):
    user_info = UserResponse.from_orm(current_user)
    
    if current_user.role == UserRole.student:
        enrollments = db.query(Enrollment).filter(Enrollment.student_id == current_user.id).all()
        courses_info = []
        for enrollment in enrollments:
            courses_info.append(StudentCourseInfo(
                course_id=enrollment.course.id,
                course_code=enrollment.course.course_code,
                title=enrollment.course.title,
                grade=enrollment.grade
            ))
        return StudentDashboard(user_info=user_info, courses=courses_info)
    
    elif current_user.role == UserRole.faculty:
        courses = db.query(Course).filter(Course.faculty_id == current_user.id).all()
        teaching_courses = [
            FacultyCourseInfo(
                course_id=course.id,
                course_code=course.course_code,
                title=course.title,
                roster_count=len(course.enrollments)
            ) for course in courses
        ]
        return FacultyDashboard(user_info=user_info, teaching_courses=teaching_courses)
    
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dashboard not available for this role")

# --- Events API ---
@app.get("/api/v1/events", response_model=List[EventResponse], tags=["Events"])
async def get_events(category: Optional[EventCategory] = None, db: DbDep = Depends(get_db)):
    query = db.query(Event)
    if category:
        query = query.filter(Event.category == category)
    events = query.order_by(Event.start_time).all()
    
    # This is N+1, but acceptable for this scale. For larger scale, use a subquery or join.
    return [EventResponse(
        **event.__dict__,
        rsvp_count=len(event.rsvps)
    ) for event in events]

@app.post("/api/v1/events/{event_id}/rsvp", status_code=status.HTTP_201_CREATED, tags=["Events"])
async def rsvp_for_event(event_id: int, current_user: CurrentUser, db: DbDep):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    existing_rsvp = db.query(RSVP).filter(RSVP.user_id == current_user.id, RSVP.event_id == event_id).first()
    if existing_rsvp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already RSVP'd")
        
    new_rsvp = RSVP(user_id=current_user.id, event_id=event_id)
    db.add(new_rsvp)
    db.commit()
    return {"message": "RSVP successful"}

# --- Gallery API ---
@app.post("/api/v1/gallery/upload", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED, tags=["Gallery"])
async def upload_photo(photo_data: PhotoUpload, current_user: CurrentUser, db: DbDep):
    if not photo_data.consent_given:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consent must be given to upload photo")
    
    new_photo = GalleryPhoto(
        uploader_id=current_user.id,
        **photo_data.model_dump()
    )
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)
    return new_photo

@app.get("/api/v1/gallery", response_model=List[PhotoResponse], tags=["Gallery"])
async def get_gallery_photos(event_tag: Optional[str] = None, academic_year: Optional[str] = None, db: DbDep = Depends(get_db)):
    query = db.query(GalleryPhoto)
    if event_tag:
        query = query.filter(GalleryPhoto.event_tag == event_tag)
    if academic_year:
        query = query.filter(GalleryPhoto.academic_year == academic_year)
    photos = query.order_by(GalleryPhoto.uploaded_at.desc()).all()
    return photos

# --- Resources API ---
@app.get("/api/v1/resources", response_model=List[ResourceResponse], tags=["Resources"])
async def search_resources(
    query: Optional[str] = None, 
    category: Optional[ResourceCategory] = None, 
    tag: Optional[str] = None, 
    db: DbDep = Depends(get_db)
):
    db_query = db.query(Resource)
    if category:
        db_query = db_query.filter(Resource.category == category)
    if query:
        db_query = db_query.filter(Resource.name.ilike(f"%{query}%") | Resource.description.ilike(f"%{query}%"))
    if tag:
        db_query = db_query.filter(Resource.tags.ilike(f"%{tag}%"))
    
    resources = db_query.all()
    return resources

# --- Feedback API ---
@app.post("/api/v1/feedback", status_code=status.HTTP_201_CREATED, tags=["Feedback"])
async def submit_anonymous_feedback(feedback: FeedbackCreate, db: DbDep):
    new_feedback = Feedback(content=feedback.content)
    db.add(new_feedback)
    db.commit()
    return {"message": "Feedback submitted successfully. Thank you."}

# --- Courses API ---
@app.get("/api/v1/courses/{course_id}", response_model=CourseDetailResponse, tags=["Courses"])
async def get_course_details(course_id: int, current_user: CurrentUser, db: DbDep):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Check if user is enrolled or is the faculty for the course
    is_faculty = course.faculty_id == current_user.id
    is_enrolled = db.query(Enrollment).filter(
        Enrollment.course_id == course_id, 
        Enrollment.student_id == current_user.id
    ).first() is not None

    if not is_faculty and not is_enrolled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to view this course")

    roster_members = []
    for enrollment in course.enrollments:
        student = enrollment.student
        roster_members.append(RosterMember(
            student_id=student.id,
            full_name=student.full_name,
            chosen_name=student.chosen_name,
            pronouns=student.pronouns
        ))
    
    # Manually construct the response to include the roster
    response_data = CourseDetailResponse(
        id=course.id,
        title=course.title,
        course_code=course.course_code,
        syllabus=course.syllabus,
        faculty=UserResponse.from_orm(course.faculty),
        roster=roster_members
    )
    return response_data

# --- Example of how to run with uvicorn ---
if __name__ == "__main__":
    import uvicorn
    print("Starting server... Access Swagger UI at http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)