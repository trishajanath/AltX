# models.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# --- Task Models ---

class TaskBase(BaseModel):
    """
    Base model for Task, containing common fields that are mutable.
    """
    title: str = Field(..., min_length=1, max_length=200, description="The title of the task.")
    completed: bool = Field(False, description="Whether the task has been completed.")

class TaskCreate(TaskBase):
    """
    Model for creating a new Task.
    Inherits all fields from TaskBase, as 'id' and 'created_at' are server-generated.
    """
    pass

class TaskUpdate(BaseModel):
    """
    Model for updating an existing Task.
    All fields are optional, allowing for partial updates.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="The updated title of the task.")
    completed: Optional[bool] = Field(None, description="The updated completion status of the task.")

class TaskResponse(TaskBase):
    """
    Model for responding with a Task, including server-generated fields.
    """
    id: str = Field(..., description="The unique identifier of the task.")
    created_at: datetime = Field(..., description="The timestamp when the task was created.")

    class Config:
        # Pydantic v2 uses model_config for configuration
        # This example shows how to configure schema extra for OpenAPI documentation
        # For ORM_MODE (from Pydantic v1), in v2 it's `from_attributes=True`
        # If you were loading from an ORM, you'd add:
        # model_config = {'from_attributes': True}
        schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "title": "Buy groceries",
                "completed": False,
                "created_at": "2023-10-27T10:00:00.000Z"
            }
        }

# Example of how to use TaskResponse as the primary "Task" model if preferred
# class Task(TaskResponse):
#     pass