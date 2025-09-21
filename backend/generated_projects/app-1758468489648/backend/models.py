from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime, timezone
from uuid import UUID, uuid4

# Define the allowed categories for college events
# Using Literal provides strong typing and validation for specific string values
EventType = Literal["Workshop", "Social", "Academic", "Career Fair", "Sports", "Club Meeting"]

class EventBase(BaseModel):
    """
    Base model for an event, containing fields common to creation and reading.
    """
    title: str = Field(..., min_length=3, max_length=100, description="The main title of the event.")
    description: Optional[str] = Field(None, max_length=500, description="A detailed description of the event.")
    event_date: datetime = Field(..., description="The date and time of the event (ISO 8601 format).")
    location: str = Field(..., min_length=3, max_length=100, description="The location of the event (e.g., 'Main Auditorium').")
    organizer: str = Field(..., min_length=3, max_length=100, description="The club or department organizing the event.")
    category: EventType = Field(..., description="The category of the event.")

    class Config:
        # Pydantic configuration to work with ORMs (though not used here, it's good practice)
        orm_mode = True
        # Provides example data in the OpenAPI documentation
        schema_extra = {
            "example": {
                "title": "Annual Computer Science Hackathon",
                "description": "Join us for a 24-hour coding competition. Food and drinks provided!",
                "event_date": "2024-10-26T09:00:00Z",
                "location": "Engineering Building, Room 301",
                "organizer": "Computer Science Club",
                "category": "Academic"
            }
        }

class EventCreate(EventBase):
    """
    Model used for creating a new event. Inherits all fields from EventBase.
    Includes a validator to ensure the event date is in the future.
    """
    @validator('event_date')
    def event_date_must_be_in_the_future(cls, v):
        if v.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError('Event date must be in the future')
        return v

class EventUpdate(BaseModel):
    """
    Model used for updating an existing event. All fields are optional.
    This allows for partial updates (PATCH-like behavior with PUT).
    """
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    event_date: Optional[datetime]
    location: Optional[str] = Field(None, min_length=3, max_length=100)
    organizer: Optional[str] = Field(None, min_length=3, max_length=100)
    category: Optional[EventType]

    @validator('event_date')
    def event_date_must_be_in_the_future(cls, v):
        if v and v.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError('Event date must be in the future')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Updated Hackathon Title",
                "location": "New Engineering Building, Main Hall"
            }
        }

class Event(EventBase):
    """
    The full event model, including system-generated fields.
    This model is used for responses from the API.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the event.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of event creation.")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of last event update.")