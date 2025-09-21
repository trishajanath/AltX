# models.py
# Pydantic models for data validation and serialization

import ulid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional

# Helper function to generate a sortable, unique ID (ULID)
def generate_ulid():
    return ulid.new().str

class Task(BaseModel):
    """
    Base model for a Task. This represents the full Task object stored in the database.
    It includes all fields, both user-provided and system-generated.
    """
    id: str = Field(default_factory=generate_ulid, alias="_id")
    title: str = Field(..., description="The main title of the task.")
    description: Optional[str] = Field(None, description="An optional detailed description of the task.")
    completed: bool = Field(False, description="Indicates whether the task has been completed.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        # Allows Pydantic to work with non-dict objects (e.g., ORM models)
        from_attributes = True
        # Enables population by field name OR alias
        populate_by_name = True
        # Example for OpenAPI documentation
        json_schema_extra = {
            "example": {
                "_id": "01H8XGJWBWBAQ4E5F9N5JAF3A2",
                "title": "Buy groceries",
                "description": "Milk, Bread, Cheese, and Eggs",
                "completed": False,
                "created_at": "2023-08-22T14:30:00Z"
            }
        }

class TaskCreate(BaseModel):
    """
    Model for creating a new Task.
    It only includes fields that the user is allowed to provide.
    This prevents users from setting system-controlled fields like 'id' or 'created_at'.
    """
    title: str = Field(
        ..., 
        min_length=3, 
        max_length=100,
        description="Task title must be between 3 and 100 characters."
    )
    description: Optional[str] = Field(
        None, 
        max_length=500,
        description="Optional description, max 500 characters."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Schedule dentist appointment",
                "description": "Call Dr. Smith's office for a check-up."
            }
        }

class TaskUpdate(BaseModel):
    """
    Model for updating an existing Task.
    All fields are optional, allowing for partial updates (e.g., only changing the 'completed' status).
    This is used for the PUT/PATCH endpoint.
    """
    title: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=100,
        description="New task title, if changing."
    )
    description: Optional[str] = Field(
        None, 
        max_length=500,
        description="New description, if changing."
    )
    completed: Optional[bool] = Field(
        None, 
        description="Update the completion status of the task."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Schedule annual dentist appointment",
                "completed": True
            }
        }