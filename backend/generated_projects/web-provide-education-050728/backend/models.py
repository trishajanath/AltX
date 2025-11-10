from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ===============================================================================
# Enums
# ===============================================================================

class UserRole(str, Enum):
    """Enumeration for user roles."""
    student = "student"
    instructor = "instructor"
    admin = "admin"


# ===============================================================================
# User Models
# ===============================================================================

# --- Base Model ---
# Contains fields that are shared across other User models.
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="john.doe@example.com")
    full_name: str = Field(..., min_length=2, max_length=100, example="John Doe")
    role: UserRole = Field(..., example=UserRole.student)


# --- Create Model ---
# Used for creating a new user. Inherits from UserBase and adds a password field.
# The password will be hashed in the business logic before storing.
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="a_very_strong_password")


# --- Update Model ---
# Used for updating an existing user. All fields are optional.
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, example="john.doe@example.com")
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, example="John Doe")
    role: Optional[UserRole] = Field(None, example=UserRole.student)
    password: Optional[str] = Field(None, min_length=8, example="a_new_strong_password")


# --- Response Model ---
# This is the model that will be returned to the client.
# It includes database-generated fields like 'id' and 'created_at'.
# It inherits from UserBase and crucially excludes any password fields for security.
class User(UserBase):
    id: UUID = Field(..., example="a1b2c3d4-e5f6-7890-1234-567890abcdef")
    created_at: datetime = Field(..., example="2023-01-01T12:00:00Z")

    # Pydantic v2 config to allow mapping from ORM models
    model_config = ConfigDict(from_attributes=True)


# ===============================================================================
# Course Models
# ===============================================================================

# --- Base Model ---
class CourseBase(BaseModel):
    course_code: str = Field(..., max_length=20, example="CS101")
    title: str = Field(..., max_length=100, example="Introduction to Computer Science")
    description: str = Field(..., example="A foundational course on programming and computer science.")
    instructor_id: UUID = Field(..., example="f0e1d2c3-b4a5-6789-0123-456789abcdef")
    start_date: date = Field(..., example="2023-09-01")
    end_date: date = Field(..., example="2023-12-15")


# --- Create Model ---
class CourseCreate(CourseBase):
    pass


# --- Update Model ---
class CourseUpdate(BaseModel):
    course_code: Optional[str] = Field(None, max_length=20, example="CS101")
    title: Optional[str] = Field(None, max_length=100, example="Introduction to Computer Science")
    description: Optional[str] = Field(None, example="A foundational course on programming and computer science.")
    instructor_id: Optional[UUID] = Field(None, example="f0e1d2c3-b4a5-6789-0123-456789abcdef")
    start_date: Optional[date] = Field(None, example="2023-09-01")
    end_date: Optional[date] = Field(None, example="2023-12-15")


# --- Response Model ---
class Course(CourseBase):
    id: UUID = Field(..., example="b1c2d3e4-f5a6-7890-1234-567890abcdef")

    model_config = ConfigDict(from_attributes=True)


# ===============================================================================
# Enrollment Models
# ===============================================================================

# --- Base Model ---
class EnrollmentBase(BaseModel):
    student_id: UUID = Field(..., example="a1b2c3d4-e5f6-7890-1234-567890abcdef")
    course_id: UUID = Field(..., example="b1c2d3e4-f5a6-7890-1234-567890abcdef")


# --- Create Model ---
class EnrollmentCreate(EnrollmentBase):
    pass


# --- Update Model ---
# Typically, only the grade would be updated for an enrollment.
# Changing student or course would mean creating a new enrollment.
class EnrollmentUpdate(BaseModel):
    final_grade: Optional[float] = Field(None, ge=0.0, le=100.0, example=88.5)


# --- Response Model ---
class Enrollment(EnrollmentBase):
    id: UUID = Field(..., example="c1d2e3f4-a5b6-7890-1234-567890abcdef")
    enrollment_date: datetime = Field(..., example="2023-09-05T10:00:00Z")
    final_grade: Optional[float] = Field(None, ge=0.0, le=100.0, example=88.5)

    model_config = ConfigDict(from_attributes=True)
