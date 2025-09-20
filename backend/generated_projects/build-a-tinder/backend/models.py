```python
import uuid
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional
from enum import Enum
from datetime import datetime

#  Enums for controlled vocabularies 

class SwipeDirection(str, Enum):
    """Enumeration for swipe actions. Ensures data consistency."""
    LEFT = "left"
    RIGHT = "right"

class Gender(str, Enum):
    """Enumeration for user gender."""
    MAN = "man"
    WOMAN = "woman"
    NON_BINARY = "non_binary"

#  Base and Common Models 

class HealthCheck(BaseModel):
    """Response model for the health check endpoint."""
    status: str = "ok"
    version: str

#  User Profile Models 

class UserProfileBase(BaseModel):
    """Base model for user profile attributes, shared between creation and response."""
    name: str = Field(..., min_length=2, max_length=50, description="User's full name")
    age: int = Field(..., gt=17, lt=100, description="User's age, must be 18 or older")
    gender: Gender
    bio: str = Field(..., max_length=500, description="A short biography of the user")
    interests: List[str] = Field(default_factory=list, max_items=10, description="List of user's interests")
    profile_picture_urls: List[str] = Field(..., min_items=1, max_items=5, description="List of URLs to profile pictures")

    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v):
        """Custom validator to ensure interests are non-empty strings."""
        if not all(isinstance(i, str) and i.strip() for i in v):
            raise ValueError('Interests must be non-empty strings')
        return [i.strip().lower() for i in v]

class UserProfileCreate(UserProfileBase):
    """Model for creating a new user profile. No additional fields for now."""
    pass

class UserProfile(UserProfileBase):
    """
    Response model for a user profile, including server-generated fields.
    This model is used when returning profile data to the client.
    """
    id: uuid.UUID = Field(..., description="Unique identifier for the user profile")
    created_at: datetime = Field(..., description="Timestamp of profile creation")

#  Swiping and Matching Models 

class SwipeAction(BaseModel):
    """Request model for performing a swipe action."""
    swiper_id: uuid.UUID = Field(..., description="The ID of the user performing the swipe")
    swiped_id: uuid.UUID = Field(..., description="The ID of the user being swiped on")
    direction: SwipeDirection

class SwipeResponse(BaseModel):
    """Response model after a swipe action."""
    status: str = "success"
    is_match: bool = Field(..., description="Indicates if the swipe resulted in a new match")
    match_id: Optional[uuid.UUID] = Field(None, description="The ID of the new match, if one occurred")

class Match(BaseModel):
    """
    Response model representing a mutual match between two users.
    """
    match_id: uuid.UUID
    user1_id: uuid.UUID
    user2_id: uuid.UUID
    matched_at: datetime
    # In a real app, you might include profile summaries here
    matched_profile: UserProfile 
```