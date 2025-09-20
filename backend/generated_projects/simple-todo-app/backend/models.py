```python
from pydantic import BaseModel, Field
from typing import Optional

"""
Pydantic models define the data structures for requests and responses.
They provide automatic data validation and documentation.
This is a critical component for ensuring data integrity and API clarity.
"""

# Base model for a Todo item.
# This contains fields that are common across different representations of a Todo.
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="The title of the todo item.")
    description: Optional[str] = Field(None, max_length=500, description="A detailed description of the todo item.")

# Model for creating a new Todo item.
# It inherits from TodoBase and does not include server-generated fields like `id` or `completed` status,
# which has a default value.
class TodoCreate(TodoBase):
    pass  # No extra fields needed for creation

# Model for updating an existing Todo item.
# All fields are optional, allowing for partial updates (e.g., updating only the title or completion status).
class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    completed: Optional[bool] = None

# The main Todo model, used for API responses.
# It includes all fields, including the server-generated `id` and `completed` status.
class Todo(TodoBase):
    id: int = Field(..., description="The unique identifier of the todo item.")
    completed: bool = Field(False, description="Indicates whether the todo item is completed.")

    # Pydantic v2 configuration
    class Config:
        # This setting allows Pydantic to work with ORM models,
        # though we are using a simple dict-based "database" here, it's a good practice.
        from_attributes = True
```