# models.py
# This file defines the Pydantic models for data validation and serialization.
# These models ensure that data conforms to a specific schema, which is a
# critical aspect of API security and reliability.

from pydantic import BaseModel, Field
from enum import Enum
import uuid

#  Enums for controlled vocabularies 

class AttendanceStatus(str, Enum):
    """
    Enum to represent the possible attendance statuses for a student.
    Using an Enum ensures that the status field can only contain valid,
    pre-defined values, preventing data inconsistency.
    """
    PRESENT = "present"
    ABSENT = "absent"
    UNMARKED = "unmarked"

#  Base and Create Models 

class StudentBase(BaseModel):
    """
    Base model for a student, containing common fields.
    """
    full_name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="The full name of the student.",
        example="Jane Doe"
    )

class StudentCreate(StudentBase):
    """
    Model used for creating a new student via the API.
    It inherits the `full_name` from StudentBase.
    This model represents the data the client sends in a POST request.
    """
    pass

#  Full Data Model 

class Student(StudentBase):
    """
    The full student model, including fields that are managed by the server.
    This model is used for API responses (e.g., in GET requests).
    """
    id: uuid.UUID = Field(..., description="The unique identifier for the student.")
    attendance_status: AttendanceStatus = Field(
        default=AttendanceStatus.UNMARKED,
        description="The current attendance status of the student."
    )

    class Config:
        """
        Pydantic model configuration.
        `orm_mode` is deprecated, use `from_attributes` for compatibility with ORMs.
        """
        from_attributes = True

#  Update Models 

class AttendanceUpdate(BaseModel):
    """
    Model used specifically for updating a student's attendance status.
    This ensures that PATCH requests only modify the intended field,
    adhering to the principle of least privilege.
    """
    status: AttendanceStatus = Field(
        ...,
        description="The new attendance status for the student.",
        example="present"
    )