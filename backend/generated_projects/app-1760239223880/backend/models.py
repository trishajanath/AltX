import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


# Base Pydantic model with ORM mode enabled
class Base(BaseModel):
    """Base model with from_attributes configuration."""
    model_config = ConfigDict(from_attributes=True)


# --- Enums ---

class UserRole(str, Enum):
    """Enumeration for user roles."""
    admin = "admin"
    manager = "manager"
    member = "member"


class AttendanceStatus(str, Enum):
    """Enumeration for attendance status."""
    present = "present"
    late = "late"
    absent = "absent"
    on_leave = "on_leave"


# --- User Models ---

class UserBase(Base):
    """Base model for User, containing common fields."""
    email: str
    full_name: str
    role: UserRole
    organization_id: uuid.UUID


class UserCreate(UserBase):
    """Model for creating a new user. Includes password."""
    password: str


class UserUpdate(Base):
    """Model for updating an existing user. All fields are optional."""
    email: str | None = None
    full_name: str | None = None
    role: UserRole | None = None
    password: str | None = None


class UserResponse(UserBase):
    """Model for returning user data in API responses."""
    id: uuid.UUID
    created_at: datetime


class UserInDB(UserResponse):
    """
    Internal model representing a user in the database.
    Includes the hashed password, which should not be exposed in API responses.
    """
    hashed_password: str


# --- Event Models ---

class EventBase(Base):
    """Base model for Event, containing common fields."""
    name: str
    description: str
    start_time: datetime
    end_time: datetime
    organization_id: uuid.UUID
    geo_latitude: float
    geo_longitude: float
    geo_radius_meters: int


class EventCreate(EventBase):
    """Model for creating a new event."""
    pass


class EventUpdate(Base):
    """Model for updating an existing event. All fields are optional."""
    name: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    geo_latitude: float | None = None
    geo_longitude: float | None = None
    geo_radius_meters: int | None = None


class EventResponse(EventBase):
    """Model for returning event data in API responses."""
    id: uuid.UUID


# --- AttendanceRecord Models ---

class AttendanceRecordBase(Base):
    """Base model for AttendanceRecord, containing common fields."""
    user_id: uuid.UUID
    event_id: uuid.UUID
    check_in_time: datetime
    check_out_time: datetime | None = None
    status: AttendanceStatus
    check_in_latitude: float
    check_in_longitude: float


class AttendanceRecordCreate(AttendanceRecordBase):
    """Model for creating a new attendance record."""
    pass


class AttendanceRecordUpdate(Base):
    """Model for updating an existing attendance record. All fields are optional."""
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    status: AttendanceStatus | None = None
    check_in_latitude: float | None = None
    check_in_longitude: float | None = None


class AttendanceRecordResponse(AttendanceRecordBase):
    """Model for returning attendance record data in API responses."""
    id: uuid.UUID