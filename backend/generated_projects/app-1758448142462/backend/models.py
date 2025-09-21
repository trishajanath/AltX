import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

# 
# Pydantic Models for Data Validation and Serialization
#
# These models define the shape of the data for API requests and responses.
# They serve as the single source of truth for your data structures and
# provide automatic validation.
# 

class RecipeBase(BaseModel):
    """Base model with common attributes for a recipe."""
    name: str = Field(
        ..., 
        min_length=3, 
        max_length=100, 
        examples=["Spaghetti Carbonara"],
        description="The title of the recipe."
    )
    ingredients: List[str] = Field(
        ..., 
        min_items=1, 
        examples=[["Pasta", "Eggs", "Pancetta", "Parmesan Cheese", "Black Pepper"]],
        description="A list of ingredients required for the recipe."
    )
    instructions: str = Field(
        ..., 
        min_length=10, 
        examples=["1. Cook pasta according to package directions. 2. ..."],
        description="Step-by-step cooking instructions."
    )
    prep_time_minutes: Optional[int] = Field(
        None, 
        ge=0, 
        examples=[10],
        description="Preparation time in minutes."
    )
    cook_time_minutes: Optional[int] = Field(
        None, 
        ge=0, 
        examples=[20],
        description="Cooking time in minutes."
    )

class RecipeCreate(RecipeBase):
    """Model used for creating a new recipe (input from user)."""
    pass

class RecipeUpdate(BaseModel):
    """Model used for updating an existing recipe. All fields are optional."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    ingredients: Optional[List[str]] = Field(None, min_items=1)
    instructions: Optional[str] = Field(None, min_length=10)
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)

class RecipeInDB(RecipeBase):
    """Model representing the full recipe object as stored in the database."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RecipeResponse(RecipeInDB):
    """Model for the recipe data sent back to the client in API responses."""
    class Config:
        # This allows the model to be created from ORM objects (if using a real ORM)
        # and helps with serialization of complex types like datetime.
        from_attributes = True

class Message(BaseModel):
    """A simple model for returning messages (e.g., error details)."""
    detail: str