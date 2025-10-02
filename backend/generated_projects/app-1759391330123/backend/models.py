from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, EmailStr, HttpUrl

# =============================================================================
# Admin User Models
# =============================================================================

class AdminUserBase(BaseModel):
    """Base model for AdminUser, contains shared fields."""
    username: str = Field(..., min_length=3, max_length=50, description="Admin's unique username")

class AdminUserCreate(AdminUserBase):
    """Model for creating a new AdminUser."""
    password: str = Field(..., min_length=8, description="Admin's password (will be hashed)")

class AdminUserUpdate(BaseModel):
    """Model for updating an existing AdminUser."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)

class AdminUser(AdminUserBase):
    """Model for representing an AdminUser, e.g., in API responses."""
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# Project Models
# =============================================================================

class ProjectBase(BaseModel):
    """Base model for Project, contains shared fields."""
    title: str = Field(..., min_length=1, max_length=100, description="Project title")
    slug: str = Field(..., min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", description="URL-friendly slug")
    description: str = Field(..., description="Detailed project description")
    technologies: List[str] = Field(..., min_items=1, description="List of technologies used")
    imageUrl: HttpUrl = Field(..., description="URL for the project's main image")
    liveUrl: Optional[HttpUrl] = Field(None, description="URL to the live project deployment")
    sourceCodeUrl: Optional[HttpUrl] = Field(None, description="URL to the project's source code repository")
    displayOrder: int = Field(0, ge=0, description="Order in which to display the project")

class ProjectCreate(ProjectBase):
    """Model for creating a new Project."""
    pass

class ProjectUpdate(BaseModel):
    """Model for updating an existing Project."""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: Optional[str] = None
    technologies: Optional[List[str]] = Field(None, min_items=1)
    imageUrl: Optional[HttpUrl] = None
    liveUrl: Optional[HttpUrl] = None
    sourceCodeUrl: Optional[HttpUrl] = None
    displayOrder: Optional[int] = Field(None, ge=0)

class Project(ProjectBase):
    """Model for representing a Project, e.g., in API responses."""
    id: int
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# Skill Models
# =============================================================================

class SkillBase(BaseModel):
    """Base model for Skill, contains shared fields."""
    name: str = Field(..., min_length=1, max_length=50, description="Name of the skill")
    category: str = Field(..., min_length=1, max_length=50, description="Category of the skill (e.g., Frontend, Backend, Database)")
    proficiency: int = Field(..., gt=0, le=100, description="Proficiency level from 1 to 100")
    iconUrl: Optional[HttpUrl] = Field(None, description="URL for the skill's icon")

class SkillCreate(SkillBase):
    """Model for creating a new Skill."""
    pass

class SkillUpdate(BaseModel):
    """Model for updating an existing Skill."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    proficiency: Optional[int] = Field(None, gt=0, le=100)
    iconUrl: Optional[HttpUrl] = None

class Skill(SkillBase):
    """Model for representing a Skill, e.g., in API responses."""
    id: int

    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# Experience Models
# =============================================================================

class ExperienceBase(BaseModel):
    """Base model for Experience, contains shared fields."""
    role: str = Field(..., min_length=1, max_length=100, description="Job title or role")
    company: str = Field(..., min_length=1, max_length=100, description="Company or organization name")
    startDate: date = Field(..., description="Start date of the experience")
    endDate: Optional[date] = Field(None, description="End date of the experience (null if current)")
    description: str = Field(..., description="Description of responsibilities and achievements")
    type: str = Field(..., min_length=1, max_length=50, description="Type of experience (e.g., Work, Education, Volunteer)")

class ExperienceCreate(ExperienceBase):
    """Model for creating a new Experience."""
    pass

class ExperienceUpdate(BaseModel):
    """Model for updating an existing Experience."""
    role: Optional[str] = Field(None, min_length=1, max_length=100)
    company: Optional[str] = Field(None, min_length=1, max_length=100)
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    description: Optional[str] = None
    type: Optional[str] = Field(None, min_length=1, max_length=50)

class Experience(ExperienceBase):
    """Model for representing an Experience, e.g., in API responses."""
    id: int

    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# Message Models
# =============================================================================

class MessageBase(BaseModel):
    """Base model for Message, contains fields submitted by a user."""
    name: str = Field(..., min_length=1, max_length=100, description="Sender's name")
    email: EmailStr = Field(..., description="Sender's email address")
    content: str = Field(..., min_length=10, max_length=5000, description="The content of the message")

class MessageCreate(MessageBase):
    """Model for creating a new Message."""
    pass

class MessageUpdate(BaseModel):
    """Model for updating an existing Message (e.g., marking as read)."""
    isRead: Optional[bool] = None

class Message(MessageBase):
    """Model for representing a Message, e.g., in API responses for the admin."""
    id: int
    isRead: bool = Field(default=False, description="Whether the message has been read by the admin")
    createdAt: datetime

    model_config = ConfigDict(from_attributes=True)