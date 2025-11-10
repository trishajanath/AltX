import enum
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ===============================================================================
# Enums
# ===============================================================================

class UserRole(str, enum.Enum):
    """Enumeration for user roles."""
    student = "student"
    faculty = "faculty"
    staff = "staff"


# ===============================================================================
# User Models
# ===============================================================================

class UserBase(BaseModel):
    """Base model for User, containing shared fields."""
    email: EmailStr
    official_name: str
    chosen_name: str
    pronouns: str
    role: UserRole
    is_active: bool = True


class UserCreate(UserBase):
    """Model for creating a new user. Includes the password."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Model for updating an existing user. All fields are optional."""
    email: Optional[EmailStr] = None
    official_name: Optional[str] = None
    chosen_name: Optional[str] = None
    pronouns: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """Response model for a user. Sent from the API to the client."""
    id: UUID

    # Pydantic V2 config to allow creating the model from ORM objects
    model_config = ConfigDict(from_attributes=True)


class UserInDB(User):
    """
    Internal model representing a user in the database, including the
    hashed password. This should not be exposed in API responses.
    """
    hashed_password: str


# ===============================================================================
# Event Models
# ===============================================================================

class EventBase(BaseModel):
    """Base model for Event, containing shared fields."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    start_time: datetime
    end_time: datetime
    location: str
    organizer_id: UUID
    tags: List[str] = Field(default_factory=list)
    accessibility_info: str


class EventCreate(EventBase):
    """Model for creating a new event."""
    pass


class EventUpdate(BaseModel):
    """Model for updating an existing event. All fields are optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    organizer_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    accessibility_info: Optional[str] = None


class Event(EventBase):
    """Response model for an event. Sent from the API to the client."""
    id: UUID

    # Pydantic V2 config to allow creating the model from ORM objects
    model_config = ConfigDict(from_attributes=True)


# ===============================================================================
# Gallery Image Models
# ===============================================================================

class GalleryImageBase(BaseModel):
    """Base model for GalleryImage, containing shared fields."""
    image_url: str
    caption: str
    uploader_id: UUID
    event_id: UUID
    consent_given: bool
    tags: List[str] = Field(default_factory=list)


class GalleryImageCreate(GalleryImageBase):
    """Model for creating a new gallery image."""
    pass


class GalleryImageUpdate(BaseModel):
    """Model for updating an existing gallery image. All fields are optional."""
    image_url: Optional[str] = None
    caption: Optional[str] = None
    consent_given: Optional[bool] = None
    tags: Optional[List[str]] = None


class GalleryImage(GalleryImageBase):
    """Response model for a gallery image. Sent from the API to the client."""
    id: UUID
    created_at: datetime

    # Pydantic V2 config to allow creating the model from ORM objects
    model_config = ConfigDict(from_attributes=True)