Answering the user's request to create a complete, production-ready FastAPI `main.py` for the "Student Attendance Management System" project.

### `main.py`

```python
# web-track-manage-661531: Student Attendance Management System
#
# This file contains the complete backend logic for the FastAPI application.
#
# To run this application:
# 1. Install dependencies:
#    pip install "fastapi[all]" sqlalchemy passlib python-jose python-multipart bcrypt
# 2. Create an 'uploads' directory in the same folder as this file.
# 3. Run the server:
#    uvicorn main:app --reload

import os
import shutil
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.exc import IntegrityError

# --- Configuration ---
# In a real production environment, load these from environment variables or a config file.
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_development_only_661531")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
DATABASE_URL = "sqlite:///./student_attendance.db"
UPLOADS_DIR = "uploads"

# Create uploads directory if it doesn't exist
os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- Security & Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Database Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Enums for Roles and Statuses ---
class UserRole(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"

class AttendanceStatus(str, Enum):
    present = "Present"
    absent = "Absent"
    late = "Late"
    excused = "Excused"

# --- SQLAlchemy Models ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    taught_courses = relationship("Course", back_populates="teacher")
    enrollments = relationship("Enrollment", back_populates="student")
    attendance_records = relationship("AttendanceRecord", back_populates="student")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    teacher = relationship("User", back_populates="taught_courses")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    sessions = relationship("ClassSession", back_populates="course", cascade="all, delete-orphan")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    enrollment_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class ClassSession(Base):
    __tablename__ = "class_sessions"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    session_datetime = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="sessions")
    attendance_records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("class_sessions.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    status = Column(SQLAlchemyEnum(AttendanceStatus), nullable=False)
    justification_text = Column(String, nullable=True)
    justification_document_url = Column(String, nullable=True)
    marked_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ClassSession", back_populates="attendance_records")
    student = relationship("User", back_populates="attendance_records")

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas (Data Transfer Objects) ---

# User & Auth Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: UserRole

class UserResponse(UserBase):
    id: int
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

# Course & Enrollment Schemas
class CourseBase(BaseModel):
    name: str
    code: str

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    teacher: UserResponse

    class Config:
        from_attributes = True

class EnrollmentResponse(BaseModel):
    id: int
    student: UserResponse
    enrollment_date: datetime

    class Config:
        from_attributes = True

class CourseDetailResponse(CourseResponse):
    enrollments: List[EnrollmentResponse] = []

# Session & Attendance Schemas
class ClassSessionCreate(BaseModel):
    course_id: int
    session_datetime: Optional[datetime] = None

class ClassSessionResponse(BaseModel):
    id: int
    course_id: int
    session_datetime: datetime

    class Config:
        from_attributes = True

class AttendanceMark(BaseModel):
    student_id: int
    status: AttendanceStatus

class AttendanceMarkingGrid(BaseModel):
    session_id: int
    marks: List[AttendanceMark]

class AttendanceRecordResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: AttendanceStatus
    justification_text: Optional[str] = None
    justification_document_url: Optional[str] = None
    marked_at: datetime
    session: ClassSessionResponse

    class Config:
        from_attributes = True

# Report Schemas
class StudentAttendanceSummary(BaseModel):
    student: UserResponse
    total_sessions: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_percentage: float

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Authentication Utilities ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- User & Role Dependencies ---
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

async def get_current_active_teacher(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher access required")
    return current_user

async def get_current_active_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

# --- FastAPI Application Setup ---
app = FastAPI(
    title="web-track-manage-661531",
    description="A minimalist web application designed for educational institutions to efficiently track and manage student attendance.",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

# Root / Health Check
@app.get("/", tags=["Root"])
async def health_check():
    return {"status": "healthy", "app": "web-track-manage-661531"}

# --- Authentication Router ---
auth_router = FastAPI(prefix="/api/v1/auth", tags=["Authentication"])

@auth_router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, email=user.email, hashed_password=hashed_password, role=user.role)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(data={"sub": new_user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": new_user
    }

@auth_router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@auth_router.post("/refresh")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    try:
        token = await request.json()
        refresh_token = token['refresh_token']
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        new_access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        return {"access_token": new_access_token, "token_type": "bearer"}

    except (JWTError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# --- Course Management Router ---
course_router = FastAPI(prefix="/api/v1/courses", tags=["Courses"])

@course_router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(course: CourseCreate, db: Session = Depends(get_db), teacher: User = Depends(get_current_active_teacher)):
    db_course = Course(**course.model_dump(), teacher_id=teacher.id)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@course_router.get("/", response_model=List[CourseResponse])
async def get_all_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.teacher:
        return db.query(Course).filter(Course.teacher_id == current_user.id).all()
    return db.query(Course).all()

@course_router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course_details(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course

@course_router.post("/{course_id}/enroll/{student_id}", response_model=EnrollmentResponse)
async def enroll_student(course_id: int, student_id: int, db: Session = Depends(get_db), teacher: User = Depends(get_current_active_teacher)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or course.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found or you are not the teacher")
    
    student = db.query(User).filter(User.id == student_id, User.role == UserRole.student).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    existing_enrollment = db.query(Enrollment).filter(Enrollment.course_id == course_id, Enrollment.student_id == student_id).first()
    if existing_enrollment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student already enrolled")

    enrollment = Enrollment(student_id=student_id, course_id=course_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment

# --- Attendance Management Router ---
attendance_router = FastAPI(prefix="/api/v1/attendance", tags=["Attendance"])

@attendance_router.post("/sessions", response_model=ClassSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_class_session(session_data: ClassSessionCreate, db: Session = Depends(get_db), teacher: User = Depends(get_current_active_teacher)):
    course = db.query(Course).filter(Course.id == session_data.course_id, Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found or you are not the teacher")
    
    new_session = ClassSession(**session_data.model_dump())
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@attendance_router.post("/mark", status_code=status.HTTP_201_CREATED)
async def mark_attendance(grid: AttendanceMarkingGrid, db: Session = Depends(get_db), teacher: User = Depends(get_current_active_teacher)):
    session = db.query(ClassSession).join(Course).filter(ClassSession.id == grid.session_id, Course.teacher_id == teacher.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or you are not authorized")

    for mark in grid.marks:
        # Check if student is enrolled
        enrollment = db.query(Enrollment).filter(Enrollment.student_id == mark.student_id, Enrollment.course_id == session.course_id).first()
        if not enrollment:
            continue # Skip students not enrolled in this course

        # Upsert logic: update if exists, create if not
        record = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == grid.session_id, AttendanceRecord.student_id == mark.student_id).first()
        if record:
            record.status = mark.status
            record.marked_at = datetime.utcnow()
        else:
            record = AttendanceRecord(session_id=grid.session_id, student_id=mark.student_id, status=mark.status)
            db.add(record)
    
    db.commit()
    return {"message": "Attendance marked successfully"}

@attendance_router.post("/justify/{attendance_id}", response_model=AttendanceRecordResponse)
async def justify_absence(
    attendance_id: int,
    justification_text: str = Form(...),
    document: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == attendance_id, AttendanceRecord.student_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
    
    if record.status not in [AttendanceStatus.absent, AttendanceStatus.late]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only justify an absence or lateness")

    record.justification_text = justification_text
    record.status = AttendanceStatus.excused # Teacher can later approve/reject this change

    if document:
        file_location = os.path.join(UPLOADS_DIR, f"{datetime.utcnow().timestamp()}_{document.filename}")
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(document.file, file_object)
        record.justification_document_url = file_location
    
    db.commit()
    db.refresh(record)
    return record

@attendance_router.get("/history/me", response_model=List[AttendanceRecordResponse])
async def get_my_attendance_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(AttendanceRecord).filter(AttendanceRecord.student_id == current_user.id).all()

# --- Reporting Router ---
report_router = FastAPI(prefix="/api/v1/reports", tags=["Reports"])

@report_router.get("/summary/course/{course_id}", response_model=List[StudentAttendanceSummary])
async def get_course_attendance_summary(course_id: int, db: Session = Depends(get_db), teacher: User = Depends(get_current_active_teacher)):
    course = db.query(Course).filter(Course.id == course_id, Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found or you are not the teacher")

    summaries = []
    total_sessions = len(course.sessions)
    if total_sessions == 0:
        return []

    for enrollment in course.enrollments:
        student = enrollment.student
        records = db.query(AttendanceRecord).join(ClassSession).filter(
            AttendanceRecord.student_id == student.id,
            ClassSession.course_id == course_id
        ).all()

        status_counts = {status.value: 0 for status in AttendanceStatus}
        for record in records:
            status_counts[record.status.value] += 1
        
        present_count = status_counts[AttendanceStatus.present] + status_counts[AttendanceStatus.late] + status_counts[AttendanceStatus.excused]
        attendance_percentage = (present_count / total_sessions) * 100 if total_sessions > 0 else 0

        summary = StudentAttendanceSummary(
            student=student,
            total_sessions=total_sessions,
            present=status_counts[AttendanceStatus.present],
            absent=status_counts[AttendanceStatus.absent],
            late=status_counts[AttendanceStatus.late],
            excused=status_counts[AttendanceStatus.excused],
            attendance_percentage=round(attendance_percentage, 2)
        )
        summaries.append(summary)
    
    return summaries

@report_router.get("/alert/send-weekly-summary/{student_id}")
async def send_weekly_summary_alert(student_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_active_admin)):
    """
    In a real application, this would be a background task triggered by a scheduler (e.g., Celery, APScheduler).
    This endpoint simulates the action of generating and sending an alert/email.
    """
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Logic to calculate weekly summary would go here.
    # For simulation, we'll just print to the console.
    print(f"--- SIMULATING WEEKLY SUMMARY EMAIL ---")
    print(f"To: {student.email}")
    print(f"Subject: Your Weekly Attendance Summary")
    print(f"Dear {student.name}, here is your attendance summary for the week...")
    print(f"---------------------------------------")

    return {"message": f"Simulated weekly summary sent to {student.email}"}


# --- Include Routers in Main App ---
app.include_router(auth_router)
app.include_router(course_router)
app.include_router(attendance_router)
app.include_router(report_router)

# --- Optional: Add a simple admin user on startup for testing ---
@app.on_event("startup")
def create_initial_admin():
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin_user:
            hashed_password = get_password_hash("adminpassword")
            new_admin = User(
                name="Admin User",
                email="admin@example.com",
                hashed_password=hashed_password,
                role=UserRole.admin
            )
            db.add(new_admin)
            db.commit()
            print("Initial admin user created with email: admin@example.com and password: adminpassword")
    finally:
        db.close()