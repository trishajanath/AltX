from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl


# ===============================================================================
# Project Models
# ===============================================================================

class ProjectBase(BaseModel):
    """
    Base model for a project, containing shared fields.
    """
    title: str
    description: str
    technologies: List[str]
    imageUrl: HttpUrl
    liveUrl: Optional[HttpUrl] = None
    repoUrl: Optional[HttpUrl] = None


class ProjectCreate(ProjectBase):
    """
    Model for creating a new project. Inherits all fields from ProjectBase.
    Used for request body validation when creating a project.
    """
    pass


class ProjectUpdate(BaseModel):
    """
    Model for updating an existing project. All fields are optional.
    Used for request body validation when updating a project (e.g., PATCH).
    """
    title: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    imageUrl: Optional[HttpUrl] = None
    liveUrl: Optional[HttpUrl] = None
    repoUrl: Optional[HttpUrl] = None


class Project(ProjectBase):
    """
    Represents a project record, typically for API responses.
    Includes the database ID and is configured for ORM mode.
    """
    id: int

    # Pydantic V2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)


# ===============================================================================
# Message Models
# ===============================================================================

class MessageBase(BaseModel):
    """
    Base model for a message, containing the core message data.
    """
    name: str
    email: EmailStr
    message: str


class MessageCreate(MessageBase):
    """
    Model for creating a new message. Inherits all fields from MessageBase.
    Used for request body validation when a user submits a message.
    """
    pass


class MessageUpdate(BaseModel):
    """
    Model for updating a message. This is less common for contact forms
    but included for completeness. All fields are optional.
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    message: Optional[str] = None


class Message(MessageBase):
    """
    Represents a message record, typically for API responses.
    Includes the database ID and submission timestamp.
    Configured for ORM mode.
    """
    id: int
    submitted_at: datetime

    # Pydantic V2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)