An Education Management System designed to streamline course administration. It provides a centralized platform for instructors to manage courses, assignments, and grades, while offering students a clear and intuitive interface to access materials, submit work, and track their academic progress.

**To run this file:**

1.  **Install dependencies:**
    ```bash
    pip install "fastapi[all]" sqlalchemy passlib[bcrypt] python-jose[cryptography] python-multipart
    ```

2.  **Set the JWT Secret Key:**
    It's recommended to set this as an environment variable for production.
    ```bash
    export JWT_SECRET_KEY='your_super_secret_key_here'
    ```
    If not set, a default (less secure) key will be used.

3.  **Run the FastAPI server:**
    ```bash
    uvicorn main:app --reload
    ```

4.  **Access the API documentation:**
    Open your browser and go to `http://127.0.0.1:8000/docs` to see the interactive Swagger UI.

```python
# main.py
# Filename: main.py
# Project: web-provide-education-050728

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
                        Enum, ForeignKey, Float)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.sql import func
import enum

# --- Configuration ---
# For production, use environment variables.
# Example: export JWT_SECRET_KEY='your_super_secret_key_here'
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "a_very_secret_key_for_development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./education_management.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Security & Authentication ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Enums ---
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"

# --- SQLAlchemy Models ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    courses_taught = relationship("Course", back_populates="instructor")
    enrollments = relationship("Enrollment", back_populates="student")
    submissions = relationship("Submission", back_populates="student")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    instructor_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    instructor = relationship("User", back_populates="courses_taught")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="course", cascade="all, delete-orphan")
    announcements = relationship("Announcement", back_populates="course", cascade="all, delete-orphan")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrollment_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    weight = Column(Float, default=1.0) # For weighted grade calculation

    # Relationships
    course = relationship("Course", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submission_time = Column(DateTime(timezone=True), server_default=func.now())
    file_path = Column(String, nullable=True) # In a real app, this would be a link to S3/blob storage
    content = Column(Text, nullable=True)

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    grade = relationship("Grade", back_populates="submission", uselist=False, cascade="all, delete-orphan")

class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False, unique=True)
    score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    graded_by_id = Column(Integer, ForeignKey("users.id"))
    graded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    submission = relationship("Submission", back_populates="grade")

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    type = Column(String) # e.g., 'pdf', 'link', 'pptx'
    url = Column(String, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)

    # Relationships
    course = relationship("Course", back_populates="resources")

class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    course = relationship("Course", back_populates="announcements")

# --- Pydantic Schemas ---

# User Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.STUDENT

class UserResponse(UserBase):
    id: int
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# Course Schemas
class CourseBase(BaseModel):
    name: str
    description: Optional[str] = None

class CourseCreate(CourseBase):
    instructor_id: int

class CourseResponse(CourseBase):
    id: int
    instructor: UserResponse
    created_at: datetime

    class Config:
        from_attributes = True

# Assignment Schemas
class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    weight: float = Field(1.0, gt=0)

class AssignmentCreate(AssignmentBase):
    pass

class AssignmentResponse(AssignmentBase):
    id: int
    course_id: int

    class Config:
        from_attributes = True

# Submission Schemas
class SubmissionCreate(BaseModel):
    content: Optional[str] = None
    file_path: Optional[str] = None # In a real app, you'd handle file uploads

class SubmissionResponse(BaseModel):
    id: int
    submission_time: datetime
    student_id: int
    assignment_id: int
    content: Optional[str] = None
    file_path: Optional[str] = None

    class Config:
        from_attributes = True

# Grade Schemas
class GradeCreate(BaseModel):
    submission_id: int
    score: float = Field(..., ge=0)
    feedback: Optional[str] = None

class GradeResponse(BaseModel):
    id: int
    score: float
    feedback: Optional[str] = None
    graded_at: datetime
    submission_id: int

    class Config:
        from_attributes = True

# Resource Schemas
class ResourceCreate(BaseModel):
    title: str
    type: str
    url: str

class ResourceResponse(ResourceCreate):
    id: int
    course_id: int

    class Config:
        from_attributes = True

# Announcement Schemas
class AnnouncementCreate(BaseModel):
    title: str
    content: str

class AnnouncementResponse(AnnouncementCreate):
    id: int
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Dashboard Schemas
class DashboardCourse(BaseModel):
    id: int
    name: str
    instructor_name: str

class DashboardAssignment(BaseModel):
    id: int
    title: str
    due_date: datetime
    course_name: str

class DashboardGrade(BaseModel):
    assignment_title: str
    course_name: str
    score: float
    graded_at: datetime

class DashboardResponse(BaseModel):
    enrolled_courses: List[DashboardCourse]
    upcoming_assignments: List[DashboardAssignment]
    recent_grades: List[DashboardGrade]
    recent_announcements: List[AnnouncementResponse]

# Gradebook Schemas
class GradebookEntry(BaseModel):
    student_id: int
    student_name: str
    assignment_id: int
    assignment_title: str
    submission_id: Optional[int] = None
    score: Optional[float] = None
    submission_time: Optional[datetime] = None

class GradeAnalyticsResponse(BaseModel):
    class_average: float
    grade_distribution: Dict[str, int] # e.g., {"A": 5, "B": 10, "C": 8}

# --- FastAPI App Initialization ---
app = FastAPI(
    title="web-provide-education-050728",
    description="A modern, web-based Education Management System designed to streamline course administration for educational institutions.",
    version="1.0.0"
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"Request: {request.method} {request.url.path} - Completed in {process_time:.4f}s - Status: {response.status_code}"
    )
    return response

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    # Create a default admin user if one doesn't exist
    db = SessionLocal()
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        hashed_password = pwd_context.hash("adminpassword")
        default_admin = User(
            name="Admin User",
            email="admin@example.com",
            hashed_password=hashed_password,
            role=UserRole.ADMIN
        )
        db.add(default_admin)
        db.commit()
        logger.info("Default admin user created.")
    db.close()

# --- Authentication Functions ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_access_token(data: dict):
    return create_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(data: dict):
    return create_token(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
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

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # This can be expanded to check if a user is active/not banned
    return current_user

def get_role_checker(allowed_roles: List[UserRole]):
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return current_user
    return role_checker

# --- API Endpoints ---

# Health Check
@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "app": "web-provide-education-050728"}

# --- Authentication Routes ---
auth_router = FastAPI()

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(name=user.name, email=user.email, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@auth_router.post("/login", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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
async def refresh_token(token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=UserResponse, tags=["Authentication"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# --- Course Management Routes ---
course_router = FastAPI()

@course_router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, tags=["Courses"])
async def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_role_checker([UserRole.ADMIN, UserRole.INSTRUCTOR]))
):
    instructor = db.query(User).filter(User.id == course.instructor_id, User.role == UserRole.INSTRUCTOR).first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    
    db_course = Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@course_router.get("/", response_model=List[CourseResponse], tags=["Courses"])
async def get_all_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    return courses

@course_router.get("/{course_id}", response_model=CourseResponse, tags=["Courses"])
async def get_course_by_id(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@course_router.post("/{course_id}/enroll", status_code=status.HTTP_204_NO_CONTENT, tags=["Courses"])
async def enroll_in_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    existing_enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == current_user.id,
        Enrollment.course_id == course_id
    ).first()
    if existing_enrollment:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")
        
    enrollment = Enrollment(student_id=current_user.id, course_id=course_id)
    db.add(enrollment)
    db.commit()
    return

# --- Dashboard Route ---
dashboard_router = FastAPI()

@dashboard_router.get("/", response_model=DashboardResponse, tags=["Dashboard"])
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Get enrolled courses
    enrollments = db.query(Enrollment).filter(Enrollment.student_id == current_user.id).all()
    course_ids = [e.course_id for e in enrollments]
    courses = db.query(Course).filter(Course.id.in_(course_ids)).all()
    dashboard_courses = [
        DashboardCourse(id=c.id, name=c.name, instructor_name=c.instructor.name) for c in courses
    ]

    # Get upcoming assignments
    now = datetime.now(timezone.utc)
    upcoming_assignments_query = db.query(Assignment, Course.name.label("course_name")).join(Course).filter(
        Assignment.course_id.in_(course_ids),
        Assignment.due_date > now
    ).order_by(Assignment.due_date).limit(5).all()
    
    upcoming_assignments = [
        DashboardAssignment(
            id=a.id, title=a.title, due_date=a.due_date, course_name=course_name
        ) for a, course_name in upcoming_assignments_query
    ]

    # Get recent grades
    recent_grades_query = db.query(Grade, Assignment.title, Course.name).join(Submission).join(Assignment).join(Course).filter(
        Submission.student_id == current_user.id
    ).order_by(Grade.graded_at.desc()).limit(5).all()

    recent_grades = [
        DashboardGrade(
            assignment_title=a_title, course_name=c_name, score=g.score, graded_at=g.graded_at
        ) for g, a_title, c_name in recent_grades_query
    ]

    # Get recent announcements
    recent_announcements = db.query(Announcement).filter(
        Announcement.course_id.in_(course_ids)
    ).order_by(Announcement.created_at.desc()).limit(5).all()

    return DashboardResponse(
        enrolled_courses=dashboard_courses,
        upcoming_assignments=upcoming_assignments,
        recent_grades=recent_grades,
        recent_announcements=recent_announcements
    )

# --- Assignment and Submission Routes ---
assignment_router = FastAPI()

@assignment_router.post("/", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED, tags=["Assignments"])
async def create_assignment(
    course_id: int,
    assignment: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_role_checker([UserRole.INSTRUCTOR, UserRole.ADMIN]))
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if current_user.role == UserRole.INSTRUCTOR and course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add assignments to this course")
    
    db_assignment = Assignment(**assignment.model_dump(), course_id=course_id)
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@assignment_router.get("/", response_model=List[AssignmentResponse], tags=["Assignments"])
async def get_assignments_for_course(course_id: int, db: Session = Depends(get_db)):
    assignments = db.query(Assignment).filter(Assignment.course_id == course_id).all()
    return assignments

@assignment_router.post("/{assignment_id}/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED, tags=["Submissions"])
async def submit_assignment(
    course_id: int,
    assignment_id: int,
    submission: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_role_checker([UserRole.STUDENT]))
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id, Assignment.course_id == course_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found in this course")
    
    if datetime.now(timezone.utc) > assignment.due_date:
        raise HTTPException(status_code=400, detail="Assignment deadline has passed")

    existing_submission = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.student_id == current_user.id
    ).first()
    if existing_submission:
        raise HTTPException(status_code=400, detail="You have already submitted this assignment")

    db_submission = Submission(
        **submission.model_dump(),
        assignment_id=assignment_id,
        student_id=current_user.id
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

# --- Gradebook Routes ---
gradebook_router = FastAPI()

@gradebook_router.post("/grade", response_model=GradeResponse, status_code=status.HTTP_201_CREATED, tags=["Gradebook"])
async def grade_submission(
    course_id: int,
    grade: GradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_role_checker([UserRole.INSTRUCTOR, UserRole.ADMIN]))
):
    submission = db.query(Submission).join(Assignment).filter(
        Submission.id == grade.submission_id,
        Assignment.course_id == course_id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found for this course")
    
    if submission.assignment.course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to grade for this course")

    existing_grade = db.query(Grade).filter(Grade.submission_id == grade.submission_id).first()
    if existing_grade:
        # Update existing grade
        existing_grade.score = grade.score
        existing_grade.feedback = grade.feedback
        existing_grade.graded_by_id = current_user.id
        existing_grade.graded_at = datetime.now(timezone.utc)
        db_grade = existing_grade
    else:
        # Create new grade
        db_grade = Grade(**grade.model_dump(), graded_by_id=current_user.id)
        db.add(db_grade)
    
    db.commit()
    db.refresh(db_grade)
    return db_grade

@gradebook_router.get("/", response_model=List[GradebookEntry], tags=["Gradebook"])
async def get_course_gradebook(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_role_checker([UserRole.INSTRUCTOR, UserRole.ADMIN]))
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to view this gradebook")

    enrollments = db.query(Enrollment).filter(Enrollment.course_id == course_id).all()
    assignments = db.query(Assignment).filter(Assignment.course_id == course_id).all()
    
    gradebook = []
    for enrollment in enrollments:
        student = enrollment.student
        for assignment in assignments:
            submission = db.query(Submission).filter(
                Submission.student_id == student.id,
                Submission.assignment_id == assignment.id
            ).first()
            
            entry = GradebookEntry(
                student_id=student.id,
                student_name=student.name,
                assignment_id=assignment.id,
                assignment_title=assignment.title,
            )
            if submission:
                entry.submission_id = submission.id
                entry.submission_time = submission.submission_time
                if submission.grade:
                    entry.score = submission.grade.score
            gradebook.append(entry)
    return gradebook

@gradebook_router.get("/analytics", response_model=GradeAnalyticsResponse, tags=["Gradebook"])
async def get_grade_analytics(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_role_checker([UserRole.INSTRUCTOR, UserRole.ADMIN]))
):
    grades = db.query(Grade.score).join(Submission).join(Assignment).filter(
        Assignment.course_id == course_id
    ).all()

    if not grades:
        return GradeAnalyticsResponse(class_average=0.0, grade_distribution={})

    scores = [g.score for g in grades]
    class_average = sum(scores) / len(scores)

    distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for score in scores:
        if score >= 90:
            distribution["A"] += 1
        elif score >= 80:
            distribution["B"] += 1
        elif score >= 70:
            distribution["C"] += 1
        elif score >= 60:
            distribution["D"] += 1
        else:
            distribution["F"] += 1
            
    return GradeAnalyticsResponse(class_average=round(class_average, 2), grade_distribution=distribution)

# --- Resource and Announcement Routes ---
resource_router = FastAPI()
announcement_router = FastAPI()

@resource_router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED, tags=["Resources"])
async def create_resource(
    course_id: int,
    resource: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_role_checker([UserRole.INSTRUCTOR, UserRole.ADMIN]))
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or (course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_resource = Resource(**resource.model_dump(), course_id=course_id)
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource

@announcement_router.post("/", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED, tags=["Announcements"])
async def create_announcement(
    course_id: int,
    announcement: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_role_checker([UserRole.INSTRUCTOR, UserRole.ADMIN]))
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or (course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_announcement = Announcement(**announcement.model_dump(), course_id=course_id)
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    return db_announcement

# --- Include Routers in Main App ---
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(course_router, prefix="/api/v1/courses")
app.include_router(dashboard_router, prefix="/api/v1/dashboard")
app.include_router(assignment_router, prefix="/api/v1/courses/{course_id}/assignments")
app.include_router(gradebook_router, prefix="/api/v1/courses/{course_id}/gradebook")
app.include_router(resource_router, prefix="/api/v1/courses/{course_id}/resources")
app.include_router(announcement_router, prefix="/api/v1/courses/{course_id}/announcements")

# Note on Rate Limiting:
# For a production environment, consider adding rate limiting to prevent abuse.
# Libraries like `slowapi` can be integrated easily.
# Example:
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# limiter = Limiter(key_func=get_remote_address)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# @app.post("/login")
# @limiter.limit("5/minute")
# async def login(...): ...