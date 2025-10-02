from datetime import date, datetime
from typing import List

from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl, Field


# =============================================================================
# Project Schemas
# =============================================================================

class ProjectBase(BaseModel):
    """Base schema for a project, containing common attributes."""
    title: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="The title of the construction project."
    )
    description: str = Field(
        ...,
        min_length=20,
        description="A detailed description of the project."
    )
    category: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Project category (e.g., 'Residential', 'Commercial', 'Industrial')."
    )
    coverImageURL: HttpUrl = Field(
        ...,
        description="URL for the project's main cover image."
    )
    imageGalleryURLs: List[HttpUrl] = Field(
        default=[],
        description="A list of image URLs for the project gallery."
    )
    completionDate: date = Field(
        ...,
        description="The date when the project was completed."
    )


class ProjectCreate(ProjectBase):
    """Schema for creating a new project. Inherits all fields from ProjectBase."""
    pass


class Project(ProjectBase):
    """
    Schema for representing a project, including database-generated fields.
    Used for API responses.
    """
    id: int = Field(..., description="The unique identifier for the project.")

    model_config = ConfigDict(
        from_attributes=True,
    )


# =============================================================================
# Contact Inquiry Schemas
# =============================================================================

class ContactInquiryBase(BaseModel):
    """Base schema for a contact inquiry."""
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the person making the inquiry."
    )
    email: EmailStr = Field(
        ...,
        description="Email address of the inquirer."
    )
    phone: str = Field(
        ...,
        min_length=7,
        max_length=20,
        description="Phone number of the inquirer."
    )
    message: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="The message content of the inquiry."
    )


class ContactInquiryCreate(ContactInquiryBase):
    """Schema for receiving a new contact inquiry via the API."""
    pass


class ContactInquiry(ContactInquiryBase):
    """
    Schema for representing a contact inquiry, including server-generated fields.
    Used for API responses.
    """
    timestamp: datetime = Field(
        ...,
        description="The date and time when the inquiry was received."
    )

    model_config = ConfigDict(
        from_attributes=True,
    )