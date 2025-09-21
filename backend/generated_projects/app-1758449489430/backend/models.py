import uuid
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum
from typing import Optional

class EventCategory(str, Enum):
    """
    Enum for categorizing college events. This ensures data consistency
    and provides a predefined list of valid categories.
    """
    ACADEMIC = "Academic"
    SPORTS = "Sports"
    CULTURAL = "Cultural"
    WORKSHOP = "Workshop"
    SOCIAL = "Social"
    CAREER = "Career Fair"

class EventBase(BaseModel):
    """
    Base Pydantic model for an event. Contains fields common to both
    creating and reading events.
    """
    title: str = Field(..., min_length=3, max_length=100, description="The title of the event.")
    description: str = Field(..., min_length=10, max_length=500, description="A detailed description of the event.")
    event_datetime: datetime = Field(..., description="The date and time of the event (ISO 8601 format).")
    location: str = Field(..., min_length=3, max_length=100, description="The location of the event (e.g., 'Main Auditorium').")
    category: EventCategory = Field(..., description="The category of the event.")
    organizer: str = Field(..., min_length=2, max_length=100, description="The organizing club or department.")
    
    class Config:
        # Allows the model to be created from ORM objects (if we were using a database)
        # and enables usage of enums for values.
        from_attributes = True
        use_enum_values = True

class EventCreate(EventBase):
    """
    Model used for creating a new event. It inherits all fields from EventBase.
    Includes custom validation logic specific to event creation.
    """
    
    @validator('event_datetime')
    def event_must_be_in_future(cls, v):
        """
        Pydantic validator to ensure that a new event cannot be created for a past date.
        This enforces a key business rule.
        """
        if v < datetime.now():
            raise ValueError('Event date and time must be in the future.')
        return v

class Event(EventBase):
    """
    Model for representing an event returned from the API.
    It includes all fields from EventBase plus a unique system-generated ID.
    """
    id: uuid.UUID = Field(..., description="The unique identifier for the event.")

# A simple model for the health check response for clear API contracts.
class HealthCheck(BaseModel):
    status: str = Field(..., example="ok")