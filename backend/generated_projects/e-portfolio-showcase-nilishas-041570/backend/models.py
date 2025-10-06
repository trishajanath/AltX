from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# =============================================================================
# Project Models
# =============================================================================

class ProjectBase(BaseModel):
    """Base model for a project, containing common fields."""
    title: str
    slug: str
    description: str
    case_study_content: str
    image_url: str
    live_demo_url: str
    source_code_url: str
    tags: List[str] = []
    display_order: int


class ProjectCreate(ProjectBase):
    """Model for creating a new project. Inherits all fields from ProjectBase."""
    pass


class ProjectUpdate(BaseModel):
    """
    Model for updating an existing project.
    All fields are optional.
    """
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    case_study_content: Optional[str] = None
    image_url: Optional[str] = None
    live_demo_url: Optional[str] = None
    source_code_url: Optional[str] = None
    tags: Optional[List[str]] = None
    display_order: Optional[int] = None


class Project(ProjectBase):
    """
    Response model for a project.
    Includes the database-generated ID and is configured for ORM mode.
    """
    id: int

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# TimelineEvent Models
# =============================================================================

class TimelineEventBase(BaseModel):
    """Base model for a timeline event."""
    type: Literal['education', 'experience']
    title: str
    institution: str
    start_date: date
    end_date: Optional[date] = None
    description: str


class TimelineEventCreate(TimelineEventBase):
    """Model for creating a new timeline event."""
    pass


class TimelineEventUpdate(BaseModel):
    """
    Model for updating an existing timeline event.
    All fields are optional.
    """
    type: Optional[Literal['education', 'experience']] = None
    title: Optional[str] = None
    institution: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class TimelineEvent(TimelineEventBase):
    """
    Response model for a timeline event.
    Includes the database-generated ID and is configured for ORM mode.
    """
    id: int

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ContactMessage Models
# =============================================================================

class ContactMessageBase(BaseModel):
    """Base model for a contact message, containing user-submitted fields."""
    sender_name: str
    sender_email: EmailStr
    message_body: str


class ContactMessageCreate(ContactMessageBase):
    """
    Model for receiving a new contact message from a user.
    This is the expected input schema.
    """
    pass


class ContactMessage(ContactMessageBase):
    """
    Response model for a contact message.
    Includes the server-generated timestamp.
    This model represents the full message object as stored or processed.
    Note: An 'Update' model is omitted as contact messages are typically immutable.
    """
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)