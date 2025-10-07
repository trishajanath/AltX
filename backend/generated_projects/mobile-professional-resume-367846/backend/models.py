from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl

# ==============================================================================
# Profile Models
# ==============================================================================

# Base model with common fields for Profile
class ProfileBase(BaseModel):
    """Base Pydantic model for Profile, containing shared fields."""
    full_name: str
    job_title: str
    summary: str
    email: EmailStr
    linkedin_url: HttpUrl
    github_url: HttpUrl
    profile_image_url: HttpUrl

# Model for creating a new Profile (inherits from Base)
class ProfileCreate(ProfileBase):
    """Model for creating a new Profile. All fields are required."""
    pass

# Model for updating an existing Profile (all fields are optional)
class ProfileUpdate(BaseModel):
    """Model for updating a Profile. All fields are optional."""
    full_name: str | None = None
    job_title: str | None = None
    summary: str | None = None
    email: EmailStr | None = None
    linkedin_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    profile_image_url: HttpUrl | None = None

# Response model for a Profile (includes database-generated fields like id)
class Profile(ProfileBase):
    """Response model for a Profile, including the database ID."""
    id: int

    # Pydantic v2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Experience Models
# ==============================================================================

# Base model with common fields for Experience
class ExperienceBase(BaseModel):
    """Base Pydantic model for Experience, containing shared fields."""
    company_name: str
    job_title: str
    start_date: date
    end_date: date | None = None
    location: str
    achievements: list[str]
    is_current: bool

# Model for creating a new Experience
class ExperienceCreate(ExperienceBase):
    """Model for creating a new Experience. All fields are required."""
    pass

# Model for updating an existing Experience (all fields are optional)
class ExperienceUpdate(BaseModel):
    """Model for updating an Experience. All fields are optional."""
    company_name: str | None = None
    job_title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    location: str | None = None
    achievements: list[str] | None = None
    is_current: bool | None = None

# Response model for an Experience
class Experience(ExperienceBase):
    """Response model for an Experience, including the database ID."""
    id: int

    # Pydantic v2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Project Models
# ==============================================================================

# Base model with common fields for Project
class ProjectBase(BaseModel):
    """Base Pydantic model for Project, containing shared fields."""
    title: str
    description: str
    technologies: list[str]
    image_url: HttpUrl
    project_url: HttpUrl | None = None
    repository_url: HttpUrl | None = None
    display_order: int

# Model for creating a new Project
class ProjectCreate(ProjectBase):
    """Model for creating a new Project. All fields are required."""
    pass

# Model for updating an existing Project (all fields are optional)
class ProjectUpdate(BaseModel):
    """Model for updating a Project. All fields are optional."""
    title: str | None = None
    description: str | None = None
    technologies: list[str] | None = None
    image_url: HttpUrl | None = None
    project_url: HttpUrl | None = None
    repository_url: HttpUrl | None = None
    display_order: int | None = None

# Response model for a Project
class Project(ProjectBase):
    """Response model for a Project, including the database ID."""
    id: int

    # Pydantic v2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)