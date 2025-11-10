import enum
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Enums ---

class UserRole(str, enum.Enum):
    """Enumeration for user roles."""
    student = "student"
    teacher = "teacher"
    admin = "admin"


# --- User Models ---

class UserBase(BaseModel):
    """Base model for User with shared attributes."""
    email: EmailStr = Field(..., example="john.doe@example.com")
    full_name: str = Field(..., min_length=2, max_length=100, example="John Doe")
    role: UserRole = Field(..., example=UserRole.student)


class UserCreate(UserBase):
    """Model for creating a new user. Expects a plain password."""
    password: str = Field(..., min_length=8, example="a_strong_password")


class UserUpdate(BaseModel):
    """Model for updating a user. All fields are optional."""
    email: Optional[EmailStr] = Field(None, example="john.doe@example.com")
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, example="John Doe")
    role: Optional[UserRole] = Field(None, example=UserRole.student)
    password: Optional[str] = Field(None, min_length=8, example="a_new_strong_password")


class User(UserBase):
    """Response model for a user. Excludes sensitive data like password."""
    id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")
    created_at: datetime = Field(..., example="2023-01-01T12:00:00Z")

    # Pydantic v2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)


# --- Course Models ---

class CourseBase(BaseModel):
    """Base model for Course with shared attributes."""
    course_name: str = Field(..., min_length=3, max_length=150, example="Introduction to Python")
    course_code: str = Field(..., min_length=3, max_length=20, example="CS101")
    teacher_id: UUID = Field(..., example="a2b3c4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d")
    schedule_details: dict[str, Any] = Field(..., example={"day": "Monday", "time": "10:00-12:00", "room": "A101"})


class CourseCreate(CourseBase):
    """Model for creating a new course."""
    pass


class CourseUpdate(BaseModel):
    """Model for updating a course. All fields are optional."""
    course_name: Optional[str] = Field(None, min_length=3, max_length=150, example="Advanced Python Programming")
    course_code: Optional[str] = Field(None, min_length=3, max_length=20, example="CS401")
    teacher_id: Optional[UUID] = Field(None, example="a2b3c4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d")
    schedule_details: Optional[dict[str, Any]] = Field(None, example={"day": "Wednesday", "time": "14:00-16:00"})


class Course(CourseBase):
    """Response model for a course."""
    id: UUID = Field(..., example="f1e2d3c4-b5a6-9876-5432-10fedcba9876")

    # Pydantic v2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)


# --- Enrollment Models ---

class EnrollmentBase(BaseModel):
    """Base model for Enrollment with shared attributes."""
    student_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")
    course_id: UUID = Field(..., example="f1e2d3c4-b5a6-9876-5432-10fedcba9876")


class EnrollmentCreate(EnrollmentBase):
    """Model for creating a new enrollment."""
    pass


class EnrollmentUpdate(BaseModel):
    """
    Model for updating an enrollment.
    Note: Enrollments are often deleted and re-created rather than updated.
    This model is provided for completeness.
    """
    student_id: Optional[UUID] = Field(None, example="123e4567-e89b-12d3-a456-426614174000")
    course_id: Optional[UUID] = Field(None, example="f1e2d3c4-b5a6-9876-5432-10fedcba9876")


class Enrollment(EnrollmentBase):
    """Response model for an enrollment."""
    id: UUID = Field(..., example="abcdef12-3456-7890-abcd-ef1234567890")

    # Pydantic v2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)