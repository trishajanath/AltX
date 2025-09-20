```python
import uuid
from pydantic import BaseModel, Field, HttpUrl, field_validator
from enum import Enum
from typing import List, Optional

#  Enums 

class SwipeAction(str, Enum):
    """Enumeration for swipe actions."""
    LIKE = "like"
    PASS = "pass"

#  Base Models 

class ProfileBase(BaseModel):
    """Base model for user profiles, containing common attributes."""
    name: str = Field(..., min_length=1, max_length=50, description="User's full name")
    age: int = Field(..., gt=17, description="User's age, must be 18 or older")
    bio: Optional[str] = Field(None, max_length=500, description="A short biography of the user")
    interests: List[str] = Field([], description="A list of the user's interests or hobbies")
    profile_picture_url: Optional[HttpUrl] = Field(None, description="URL to the user's profile picture")

    @field_validator('interests')
    @classmethod
    def max_interests(cls, v):
        if len(v) > 10:
            raise ValueError('Cannot have more than 10 interests')
        return v

#  Database/Response Models 

class Profile(ProfileBase):
    """
    Full profile model including a unique identifier.
    This model represents a profile as it is stored and returned by the API.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the profile")

class Match(BaseModel):
    """
    Represents a successful match between two users.
    """
    match_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the match event")
    matched_profile: Profile = Field(..., description="The profile of the user you matched with")
    timestamp: str = Field(..., description="ISO timestamp of when the match occurred")

#  Request Models 

class SwipeRequest(BaseModel):
    """
    Model for the request body when performing a swipe action.
    """
    action: SwipeAction = Field(..., description="The swipe action: 'like' or 'pass'")

#  Response Models 

class SwipeResponse(BaseModel):
    """
    Model for the response after a swipe action.
    """
    status: str = Field("success", description="Indicates the outcome of the swipe action")
    is_match: bool = Field(False, description="True if the swipe resulted in a new match")
    match_details: Optional[Match] = Field(None, description="Details of the match if one occurred")

class HealthCheck(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field("ok", description="Indicates the service is running")
```