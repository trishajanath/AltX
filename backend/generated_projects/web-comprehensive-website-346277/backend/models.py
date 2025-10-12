from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, EmailStr

# ==============================================================================
# Program Models
# ==============================================================================

class ProgramBase(BaseModel):
    """Base model for a Program, containing shared fields."""
    name: str = Field(..., min_length=3, max_length=150, description="Name of the academic program")
    department: str = Field(..., min_length=3, max_length=100, description="Department offering the program")
    degree_level: str = Field(..., max_length=50, description="e.g., Bachelor's, Master's, PhD")
    description: str = Field(..., description="A detailed description of the program")
    eligibility_criteria: Dict[str, Any] = Field(..., description="Key-value pairs of eligibility criteria")
    duration_years: int = Field(..., gt=0, le=10, description="Duration of the program in years")
    syllabus_url: HttpUrl = Field(..., description="A valid URL to the program's syllabus")


class ProgramCreate(ProgramBase):
    """Model for creating a new program. Inherits all fields from ProgramBase."""
    pass


class ProgramUpdate(BaseModel):
    """Model for updating an existing program. All fields are optional."""
    name: Optional[str] = Field(None, min_length=3, max_length=150, description="Name of the academic program")
    department: Optional[str] = Field(None, min_length=3, max_length=100, description="Department offering the program")
    degree_level: Optional[str] = Field(None, max_length=50, description="e.g., Bachelor's, Master's, PhD")
    description: Optional[str] = Field(None, description="A detailed description of the program")
    eligibility_criteria: Optional[Dict[str, Any]] = Field(None, description="Key-value pairs of eligibility criteria")
    duration_years: Optional[int] = Field(None, gt=0, le=10, description="Duration of the program in years")
    syllabus_url: Optional[HttpUrl] = Field(None, description="A valid URL to the program's syllabus")


class Program(ProgramBase):
    """Response model for a Program. Includes database-generated fields like id."""
    id: int = Field(..., description="The unique identifier for the program")

    # Pydantic V2 config to enable creating the model from ORM objects
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Faculty Models
# ==============================================================================

class FacultyBase(BaseModel):
    """Base model for a Faculty member, containing shared fields."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the faculty member")
    designation: str = Field(..., max_length=100, description="e.g., Professor, Assistant Professor")
    department: str = Field(..., max_length=100, description="Department the faculty member belongs to")
    email: EmailStr = Field(..., description="The faculty member's official email address")
    profile_image_url: HttpUrl = Field(..., description="A valid URL to the faculty member's profile image")
    qualifications: List[str] = Field(..., description="List of academic qualifications")
    research_interests: List[str] = Field(..., description="List of research interests")


class FacultyCreate(FacultyBase):
    """Model for creating a new faculty member."""
    pass


class FacultyUpdate(BaseModel):
    """Model for updating an existing faculty member. All fields are optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name of the faculty member")
    designation: Optional[str] = Field(None, max_length=100, description="e.g., Professor, Assistant Professor")
    department: Optional[str] = Field(None, max_length=100, description="Department the faculty member belongs to")
    email: Optional[EmailStr] = Field(None, description="The faculty member's official email address")
    profile_image_url: Optional[HttpUrl] = Field(None, description="A valid URL to the faculty member's profile image")
    qualifications: Optional[List[str]] = Field(None, description="List of academic qualifications")
    research_interests: Optional[List[str]] = Field(None, description="List of research interests")


class Faculty(FacultyBase):
    """Response model for a Faculty member."""
    id: int = Field(..., description="The unique identifier for the faculty member")

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Alumnus Models
# ==============================================================================

class AlumnusBase(BaseModel):
    """Base model for an Alumnus, containing shared fields."""
    full_name: str = Field(..., min_length=2, max_length=150, description="Full name of the alumnus")
    graduation_year: int = Field(..., gt=1950, description="Year of graduation")
    program_id: int = Field(..., description="Foreign key referencing the Program ID")
    current_company: str = Field(..., max_length=100, description="Current company of employment")
    current_role: str = Field(..., max_length=100, description="Current job role")
    linkedin_profile_url: HttpUrl = Field(..., description="A valid URL to the alumnus's LinkedIn profile")
    is_featured: bool = Field(default=False, description="Whether the alumnus is featured on the website")


class AlumnusCreate(AlumnusBase):
    """Model for creating a new alumnus record."""
    pass


class AlumnusUpdate(BaseModel):
    """Model for updating an existing alumnus record. All fields are optional."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=150, description="Full name of the alumnus")
    graduation_year: Optional[int] = Field(None, gt=1950, description="Year of graduation")
    program_id: Optional[int] = Field(None, description="Foreign key referencing the Program ID")
    current_company: Optional[str] = Field(None, max_length=100, description="Current company of employment")
    current_role: Optional[str] = Field(None, max_length=100, description="Current job role")
    linkedin_profile_url: Optional[HttpUrl] = Field(None, description="A valid URL to the alumnus's LinkedIn profile")
    is_featured: Optional[bool] = Field(None, description="Whether the alumnus is featured on the website")


class Alumnus(AlumnusBase):
    """Response model for an Alumnus."""
    id: int = Field(..., description="The unique identifier for the alumnus")

    model_config = ConfigDict(from_attributes=True)