from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl


# ==============================================================================
# Program Models
# ==============================================================================

class ProgramBase(BaseModel):
    """
    Base model for a Program, containing shared fields.
    """
    title: str
    department: str
    degree_level: str
    description: str
    duration_years: int
    tuition_fee: float
    session_start_date: date


class ProgramCreate(ProgramBase):
    """
    Model for creating a new Program. Inherits all fields from ProgramBase.
    Used for POST requests.
    """
    pass


class ProgramUpdate(BaseModel):
    """
    Model for updating an existing Program. All fields are optional.
    Used for PATCH requests.
    """
    title: Optional[str] = None
    department: Optional[str] = None
    degree_level: Optional[str] = None
    description: Optional[str] = None
    duration_years: Optional[int] = None
    tuition_fee: Optional[float] = None
    session_start_date: Optional[date] = None


class Program(ProgramBase):
    """
    Response model for a Program. Includes the database ID.
    Used for GET responses and represents the data from the database.
    """
    id: int

    # Pydantic V2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Faculty Models
# ==============================================================================

class FacultyBase(BaseModel):
    """
    Base model for a Faculty member, containing shared fields.
    """
    full_name: str
    title: str
    department: str
    email: EmailStr
    bio: str
    profile_image_url: HttpUrl
    research_interests: List[str] = []


class FacultyCreate(FacultyBase):
    """
    Model for creating a new Faculty member. Inherits all fields from FacultyBase.
    Used for POST requests.
    """
    pass


class FacultyUpdate(BaseModel):
    """
    Model for updating an existing Faculty member. All fields are optional.
    Used for PATCH requests.
    """
    full_name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    profile_image_url: Optional[HttpUrl] = None
    research_interests: Optional[List[str]] = None


class Faculty(FacultyBase):
    """
    Response model for a Faculty member. Includes the database ID.
    Used for GET responses and represents the data from the database.
    """
    id: int

    # Pydantic V2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# CampusEvent Models
# ==============================================================================

class CampusEventBase(BaseModel):
    """
    Base model for a Campus Event, containing shared fields.
    """
    title: str
    description: str
    event_date: datetime
    location: str
    category: str


class CampusEventCreate(CampusEventBase):
    """
    Model for creating a new Campus Event. Inherits all fields from CampusEventBase.
    Used for POST requests.
    """
    pass


class CampusEventUpdate(BaseModel):
    """
    Model for updating an existing Campus Event. All fields are optional.
    Used for PATCH requests.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    location: Optional[str] = None
    category: Optional[str] = None


class CampusEvent(CampusEventBase):
    """
    Response model for a Campus Event. Includes the database ID.
    Used for GET responses and represents the data from the database.
    """
    id: int

    # Pydantic V2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)