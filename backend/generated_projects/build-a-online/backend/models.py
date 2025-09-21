from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class HealthCheck(BaseModel):
    """
    Response model for the health check endpoint.
    """
    status: str = Field(..., example="ok")

class SongBase(BaseModel):
    """
    Base model for a song, containing common attributes.
    """
    title: str = Field(..., min_length=1, max_length=100, example="Sunset Groove")
    artist: str = Field(..., min_length=1, max_length=50, example="The Night Drivers")
    album: str = Field(..., min_length=1, max_length=100, example="Midnight City")
    duration_seconds: int = Field(..., gt=0, description="Duration of the track in seconds.", example=210)

class Song(SongBase):
    """
    Full song model, including server-generated fields like ID and URLs.
    This model is used for API responses.
    """
    id: int = Field(..., description="Unique identifier for the song.", example=1)
    album_art_url: Optional[HttpUrl] = Field(None, example="https://example.com/art/midnight-city.jpg")
    
    class Config:
        # Pydantic V1: orm_mode = True
        # Pydantic V2: from_attributes = True
        # This allows the model to be created from ORM objects (or dicts with attribute access).
        from_attributes = True