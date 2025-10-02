from pydantic import BaseModel
from datetime import datetime

# Base schema with common attributes
class EventBase(BaseModel):
    name: str
    description: str | None = None
    location: str
    start_date: datetime
    end_date: datetime

# Schema for creating an event (request body)
class EventCreate(EventBase):
    pass

# Schema for reading an event (response body)
class Event(EventBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True