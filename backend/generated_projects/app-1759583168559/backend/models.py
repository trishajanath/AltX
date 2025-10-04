from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


# =============================================================================
# Video Models
# =============================================================================

# Base model with shared properties for a Video
class VideoBase(BaseModel):
    """Shared properties for a video."""
    title: str
    description: Optional[str] = None
    video_url: HttpUrl
    thumbnail_url: HttpUrl


# Model for creating a new Video in the database (input)
class VideoCreate(VideoBase):
    """Properties to receive via API on creation."""
    pass


# Model for updating an existing Video in the database (input)
# All fields are optional for PATCH requests
class VideoUpdate(BaseModel):
    """Properties to receive via API on update."""
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[HttpUrl] = None
    thumbnail_url: Optional[HttpUrl] = None


# Full Video model, representing a record in the database (output)
class Video(VideoBase):
    """
    Full video model to be returned from the API.
    Includes the database ID.
    """
    id: int

    # Pydantic V2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Achievement Models
# =============================================================================

# Base model with shared properties for an Achievement
class AchievementBase(BaseModel):
    """Shared properties for an achievement."""
    title: str
    event_name: str
    date: date
    description: Optional[str] = None


# Model for creating a new Achievement in the database (input)
class AchievementCreate(AchievementBase):
    """Properties to receive via API on creation."""
    pass


# Model for updating an existing Achievement in the database (input)
# All fields are optional for PATCH requests
class AchievementUpdate(BaseModel):
    """Properties to receive via API on update."""
    title: Optional[str] = None
    event_name: Optional[str] = None
    date: Optional[date] = None
    description: Optional[str] = None


# Full Achievement model, representing a record in the database (output)
class Achievement(AchievementBase):
    """
    Full achievement model to be returned from the API.
    Includes the database ID.
    """
    id: int

    # Pydantic V2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)