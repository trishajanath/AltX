import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# A base model with a configuration to allow ORM mode (from_attributes=True)
# This enables Pydantic models to be created from ORM objects directly.
class Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ------------------- Enums -------------------

class AssignmentPriority(str, Enum):
    """Enum for assignment priority levels."""
    low = "low"
    medium = "medium"
    high = "high"


class AssignmentStatus(str, Enum):
    """Enum for assignment status."""
    pending = "pending"
    completed = "completed"
    overdue = "overdue"


# ------------------- Assignment Models -------------------

class AssignmentBase(Base):
    """Base schema for an assignment, containing common attributes."""
    title: str = Field(..., min_length=1, max_length=255, description="Title of the assignment")
    due_date: datetime
    priority: AssignmentPriority = AssignmentPriority.medium
    status: AssignmentStatus = AssignmentStatus.pending
    grade: Optional[float] = Field(None, ge=0, le=100, description="Grade received for the assignment (0-100)")
    notes: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    """Schema for creating a new assignment. Requires course_id."""
    course_id: uuid.UUID


class AssignmentUpdate(Base):
    """
    Schema for updating an assignment. All fields are optional.
    Inherits from Base directly to avoid making all fields from AssignmentBase required.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    due_date: Optional[datetime] = None
    priority: Optional[AssignmentPriority] = None
    status: Optional[AssignmentStatus] = None
    grade: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class AssignmentResponse(AssignmentBase):
    """Schema for returning an assignment from the API, including database-generated fields."""
    id: uuid.UUID
    course_id: uuid.UUID


# ------------------- Course Models -------------------

class CourseBase(Base):
    """Base schema for a course, containing common attributes."""
    course_name: str = Field(..., min_length=1, max_length=255)
    course_code: Optional[str] = Field(None, max_length=20)
    professor_name: Optional[str] = Field(None, max_length=100)
    credits: float = Field(..., ge=0, description="Number of credits for the course")


class CourseCreate(CourseBase):
    """
    Schema for creating a new course.
    The user_id will be inferred from the authenticated user, not passed in the request body.
    """
    pass


class CourseUpdate(Base):
    """Schema for updating a course. All fields are optional."""
    course_name: Optional[str] = Field(None, min_length=1, max_length=255)
    course_code: Optional[str] = Field(None, max_length=20)
    professor_name: Optional[str] = Field(None, max_length=100)
    credits: Optional[float] = Field(None, ge=0)


class CourseResponse(CourseBase):
    """
    Schema for returning a course from the API.
    Includes database-generated fields and a list of related assignments.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    assignments: List[AssignmentResponse] = []


# ------------------- User Models -------------------

class UserBase(Base):
    """Base schema for a user, containing common attributes."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user. Includes the password field for registration."""
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")


class UserUpdate(Base):
    """Schema for updating a user. All fields are optional."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8, description="New password (min 8 characters)")


class UserResponse(UserBase):
    """
    Schema for returning a user from the API.
    Excludes sensitive data like password_hash and includes database-generated fields
    and a list of related courses.
    """
    id: uuid.UUID
    created_at: datetime
    courses: List[CourseResponse] = []