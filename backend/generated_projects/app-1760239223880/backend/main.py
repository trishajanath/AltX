An excellent choice for a modern application. Here is a complete, production-ready `main.py` file for the "Employee & Event Attendance Management System".

This single file includes:
- A full JWT authentication system with registration, login, current user, and token refresh.
- Comprehensive database models for Users, Events, Attendance, and Leave Requests using SQLAlchemy and SQLite.
- Pydantic schemas for robust data validation.
- API endpoints for all specified features, including event management, QR code token generation, geofenced check-ins, reporting, and leave requests.
- Role-based access control (Admin vs. Employee).
- Security best practices, including password hashing, protected routes, and proper CORS configuration.

### `main.py`

```python
# main.py
# Employee & Event Attendance Management System: app-1760239223880

# --- Imports ---
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Annotated

from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (create_engine, Column, Integer, String, DateTime,
                        ForeignKey, Float, Enum, Boolean, Table)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from math import radians, cos, sin, asin, sqrt
import enum

# --- Configuration ---
# In a real production environment, use environment variables for these settings.
# Example: SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY = "a_very_secret_key_for_jwt_should_be_long_and_random"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
QR_CODE_TOKEN_EXPIRE_MINUTES = 2 # QR codes are short-lived for security

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./app_1760239223880.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Security & Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Enums for Roles and Statuses ---
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"

class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"
    ON_LEAVE = "on_leave"

# --- Association Table for Event Roster (Many-to-Many) ---
event_roster = Table(
    'event_roster', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('event_id', Integer, ForeignKey('events.id'), primary_key=True)
)

# --- SQLAlchemy Database Models ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    attendance_records = relationship("AttendanceRecord", back_populates="user")
    leave_requests = relationship("LeaveRequest", back_populates="user")
    created_events = relationship("Event", back_populates="creator")
    events = relationship("Event", secondary=event_roster, back_populates="attendees")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    geofence_radius_meters = Column(Integer, nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    creator = relationship("User", back_populates="created_events")
    attendance_records = relationship("AttendanceRecord", back_populates="event")
    attendees = relationship("User", secondary=event_roster, back_populates="events")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    check_in_lat = Column(Float, nullable=True)
    check_in_lon = Column(Float, nullable=True)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.ABSENT)

    user = relationship("User", back_populates="attendance_records")
    event = relationship("Event", back_populates="attendance_records")

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="leave_requests")

# Create database tables
Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas (Data Validation) ---

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.EMPLOYEE

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    
    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Event Schemas
class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    geofence_radius_meters: Optional[int] = None

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: int
    creator_id: int
    
    class Config:
        from_attributes = True

# Attendance Schemas
class CheckInPayload(BaseModel):
    qr_code_token: str
    latitude: float
    longitude: float

class AttendanceRecordResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: AttendanceStatus

    class Config:
        from_attributes = True

# Leave Schemas
class LeaveRequestCreate(BaseModel):
    start_date: datetime
    end_date: datetime
    reason: str

class LeaveRequestResponse(LeaveRequestCreate):
    id: int
    user_id: int
    status: LeaveStatus

    class Config:
        from_attributes = True

class LeaveStatusUpdate(BaseModel):
    status: LeaveStatus

# Dashboard & Report Schemas
class DashboardSummary(BaseModel):
    present: int
    absent: int
    late: int
    on_leave: int
    live_check_ins: List[AttendanceRecordResponse]

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Authentication & Authorization ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(data, expires)

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
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
    user = get_user_by_email(db, email=token_data.email)
    if user is None or not user.is_active:
        raise credentials_exception
    return user

async def get_current_admin_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

# --- Geofencing Helper ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points on Earth in meters."""
    R = 6371000  # Radius of Earth in meters
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    
    return R * c

# --- FastAPI App Initialization ---
app = FastAPI(
    title="app-1760239223880: Employee & Event Attendance Management System",
    description="A modern, real-time attendance tracking web application using QR codes and geofencing.",
    version="1.0.0"
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

# Root/Health Check
@app.get("/", tags=["System"])
async def health_check():
    return {"status": "healthy", "app": "app-1760239223880"}

# --- Authentication Routes ---
auth_router = app
@auth_router.post("/api/v1/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # First user registered is an admin
    user_count = db.query(User).count()
    role = UserRole.ADMIN if user_count == 0 else user.role

    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@auth_router.post("/api/v1/auth/login", response_model=Token, tags=["Authentication"])
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@auth_router.post("/api/v1/auth/refresh", response_model=Token, tags=["Authentication"])
async def refresh_token(current_user: Annotated[User, Depends(get_current_user)]):
    # This endpoint assumes the refresh token is sent as a Bearer token.
    # A more robust implementation would use a separate endpoint and header for refresh tokens.
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": current_user.email})
    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

@auth_router.get("/api/v1/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

# --- Event Management Routes ---
event_router = app
@event_router.post("/api/v1/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED, tags=["Events"])
async def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    new_event = Event(**event.model_dump(), creator_id=admin_user.id)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

@event_router.get("/api/v1/events", response_model=List[EventResponse], tags=["Events"])
async def list_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Event).all()

@event_router.get("/api/v1/events/{event_id}", response_model=EventResponse, tags=["Events"])
async def get_event_details(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@event_router.post("/api/v1/events/{event_id}/roster", status_code=status.HTTP_204_NO_CONTENT, tags=["Events"])
async def add_user_to_roster(
    event_id: int,
    user_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    user_to_add = db.query(User).filter(User.id == user_id).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")
    
    event.attendees.append(user_to_add)
    db.commit()

# --- QR Code & Attendance Routes ---
attendance_router = app
@attendance_router.get("/api/v1/events/{event_id}/qr-code", response_model=dict, tags=["Attendance"])
async def generate_qr_code_token(
    event_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    expires = timedelta(minutes=QR_CODE_TOKEN_EXPIRE_MINUTES)
    qr_token = create_access_token(
        data={"sub": f"event:{event_id}", "type": "qr_check_in"},
        expires_delta=expires
    )
    return {"qr_code_token": qr_token, "expires_in_seconds": expires.total_seconds()}

@attendance_router.post("/api/v1/attendance/check-in", response_model=AttendanceRecordResponse, tags=["Attendance"])
async def check_in(
    payload: CheckInPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        token_payload = jwt.decode(payload.qr_code_token, SECRET_KEY, algorithms=[ALGORITHM])
        if token_payload.get("type") != "qr_check_in":
            raise JWTError
        subject = token_payload.get("sub")
        event_id = int(subject.split(":")[1])
    except (JWTError, IndexError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid or expired QR code token")

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Geofence validation
    if event.location_lat and event.location_lon and event.geofence_radius_meters:
        distance = haversine_distance(
            event.location_lat, event.location_lon,
            payload.latitude, payload.longitude
        )
        if distance > event.geofence_radius_meters:
            raise HTTPException(status_code=403, detail=f"Check-in failed. You are {int(distance)}m away from the event location.")

    # Check if user is on the roster
    if event.attendees and current_user not in event.attendees:
        raise HTTPException(status_code=403, detail="You are not on the roster for this event.")

    # Check for existing check-in
    existing_record = db.query(AttendanceRecord).filter_by(user_id=current_user.id, event_id=event.id).first()
    if existing_record and existing_record.check_in_time:
        raise HTTPException(status_code=400, detail="You have already checked in for this event.")

    check_in_time = datetime.now(timezone.utc)
    
    # Determine status (late or present)
    # Assuming a 5-minute grace period
    if check_in_time > event.start_time + timedelta(minutes=5):
        status = AttendanceStatus.LATE
    else:
        status = AttendanceStatus.PRESENT

    if existing_record:
        existing_record.check_in_time = check_in_time
        existing_record.check_in_lat = payload.latitude
        existing_record.check_in_lon = payload.longitude
        existing_record.status = status
        db.commit()
        db.refresh(existing_record)
        return existing_record
    else:
        new_record = AttendanceRecord(
            user_id=current_user.id,
            event_id=event.id,
            check_in_time=check_in_time,
            check_in_lat=payload.latitude,
            check_in_lon=payload.longitude,
            status=status
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record

@attendance_router.post("/api/v1/attendance/check-out/{event_id}", response_model=AttendanceRecordResponse, tags=["Attendance"])
async def check_out(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.query(AttendanceRecord).filter_by(user_id=current_user.id, event_id=event_id).first()
    if not record or not record.check_in_time:
        raise HTTPException(status_code=404, detail="No active check-in found for this event.")
    if record.check_out_time:
        raise HTTPException(status_code=400, detail="You have already checked out.")

    record.check_out_time = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return record

# --- Dashboard & Reporting Routes ---
report_router = app
@report_router.get("/api/v1/dashboard/summary/{event_id}", response_model=DashboardSummary, tags=["Dashboard & Reports"])
async def get_dashboard_summary(
    event_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    records = db.query(AttendanceRecord).filter(AttendanceRecord.event_id == event_id).all()
    
    present_count = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    late_count = sum(1 for r in records if r.status == AttendanceStatus.LATE)
    on_leave_count = sum(1 for r in records if r.status == AttendanceStatus.ON_LEAVE)
    
    total_attendees = len(event.attendees) if event.attendees else db.query(User).count()
    absent_count = total_attendees - (present_count + late_count + on_leave_count)

    live_check_ins = db.query(AttendanceRecord).filter(AttendanceRecord.event_id == event_id).order_by(AttendanceRecord.check_in_time.desc()).limit(10).all()

    return DashboardSummary(
        present=present_count,
        absent=absent_count,
        late=late_count,
        on_leave=on_leave_count,
        live_check_ins=live_check_ins
    )

@report_router.get("/api/v1/reports/attendance", response_model=List[AttendanceRecordResponse], tags=["Dashboard & Reports"])
async def generate_attendance_report(
    event_id: Optional[int] = None,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    query = db.query(AttendanceRecord)
    if event_id:
        query = query.filter(AttendanceRecord.event_id == event_id)
    if user_id:
        query = query.filter(AttendanceRecord.user_id == user_id)
    if start_date:
        query = query.join(Event).filter(Event.start_time >= start_date)
    if end_date:
        query = query.join(Event).filter(Event.start_time <= end_date)
    
    return query.all()

# --- Leave Management Routes ---
leave_router = app
@leave_router.post("/api/v1/leave-requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED, tags=["Leave Management"])
async def submit_leave_request(
    request_data: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_request = LeaveRequest(**request_data.model_dump(), user_id=current_user.id)
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@leave_router.get("/api/v1/leave-requests", response_model=List[LeaveRequestResponse], tags=["Leave Management"])
async def get_leave_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.ADMIN:
        return db.query(LeaveRequest).all()
    return db.query(LeaveRequest).filter(LeaveRequest.user_id == current_user.id).all()

@leave_router.put("/api/v1/leave-requests/{request_id}/status", response_model=LeaveRequestResponse, tags=["Leave Management"])
async def update_leave_request_status(
    request_id: int,
    status_update: LeaveStatusUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    leave_request.status = status_update.status
    leave_request.reviewed_by_id = admin_user.id
    db.commit()
    db.refresh(leave_request)
    return leave_request

# --- How to Run ---
# 1. Install dependencies:
#    pip install "fastapi[all]" sqlalchemy passlib[bcrypt] python-jose[cryptography]
#
# 2. Save the code as main.py
#
# 3. Run the server:
#    uvicorn main:app --reload
#
# The API will be available at http://127.0.0.1:8000
# Interactive documentation (Swagger UI) at http://127.0.0.1:8000/docs