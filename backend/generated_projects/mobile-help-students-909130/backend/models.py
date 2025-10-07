import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Base Model Configuration
class CustomBaseModel(BaseModel):
    """Base Pydantic model with from_attributes enabled."""
    model_config = ConfigDict(from_attributes=True)


# --- Enums ---

class AssignmentStatus(str, Enum):
    """Enum for assignment status."""
    PENDING = "pending"
    COMPLETED = "completed"


class AssignmentPriority(str, Enum):
    """Enum for assignment priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# --- User Models ---

class UserBase(CustomBaseModel):
    """Base model for User, containing shared fields."""
    email: EmailStr


class UserCreate(UserBase):
    """Model for creating a new user. Includes password."""
    password: str


class UserUpdate(CustomBaseModel):
    """Model for updating a user. All fields are optional."""
    email: EmailStr | None = None
    password: str | None = None


class User(UserBase):
    """Response model for a user. Excludes sensitive information like password."""
    id: uuid.UUID
    created_at: datetime


# --- Course Models ---

class CourseBase(CustomBaseModel):
    """Base model for Course, containing shared fields."""
    name: str
    course_code: str | None = None
    color_hex: str = Field(..., pattern=r"^#[0-9a-fA-F]{6}$")


class CourseCreate(CourseBase):
    """Model for creating a new course."""
    pass


class CourseUpdate(CustomBaseModel):
    """Model for updating a course. All fields are optional."""
    name: str | None = None
    course_code: str | None = None
    color_hex: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


class Course(CourseBase):
    """Response model for a course."""
    id: uuid.UUID
    user_id: uuid.UUID


# --- Assignment Models ---

class AssignmentBase(CustomBaseModel):
    """Base model for Assignment, containing shared fields."""
    title: str
    description: str | None = None
    due_date: datetime
    status: AssignmentStatus = AssignmentStatus.PENDING
    priority: AssignmentPriority = AssignmentPriority.MEDIUM


class AssignmentCreate(AssignmentBase):
    """Model for creating a new assignment."""
    course_id: uuid.UUID


class AssignmentUpdate(CustomBaseModel):
    """Model for updating an assignment. All fields are optional."""
    title: str | None = None
    description: str | None = None
    due_date: datetime | None = None
    status: AssignmentStatus | None = None
    priority: AssignmentPriority | None = None
    completed_at: datetime | None = None


class Assignment(AssignmentBase):
    """Response model for an assignment."""
    id: uuid.UUID
    completed_at: datetime | None = None
    course_id: uuid.UUID
    user_id: uuid.UUID