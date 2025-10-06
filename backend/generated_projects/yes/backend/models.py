import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Enums ---

class ProposalStatus(str, Enum):
    """Enumeration for the status of a Proposal."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    COMMITTED = "COMMITTED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


# --- User Models ---

class UserBase(BaseModel):
    """Base model for User with common attributes."""
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """Model for creating a new user. Expects a plain password."""
    password: str


class UserUpdate(BaseModel):
    """Model for updating an existing user. All fields are optional."""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None  # For password change operations


class User(UserBase):
    """Response model for a User. Excludes sensitive data like password_hash."""
    id: uuid.UUID
    created_at: datetime

    # Pydantic V2 config to allow ORM model mapping
    model_config = ConfigDict(from_attributes=True)


# --- Proposal Models ---

class ProposalBase(BaseModel):
    """Base model for Proposal with common attributes."""
    title: str
    description: Optional[Any] = None  # Allows for flexible JSON content
    success_metric: str
    status: ProposalStatus = Field(default=ProposalStatus.DRAFT)


class ProposalCreate(ProposalBase):
    """Model for creating a new proposal.
    
    The creator_id will typically be derived from the authenticated user context
    in the API endpoint, not from the request body.
    """
    pass


class ProposalUpdate(BaseModel):
    """Model for updating an existing proposal. All fields are optional."""
    title: Optional[str] = None
    description: Optional[Any] = None
    success_metric: Optional[str] = None
    status: Optional[ProposalStatus] = None


class Proposal(ProposalBase):
    """Response model for a Proposal."""
    id: uuid.UUID
    creator_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Commitment Models ---

class CommitmentBase(BaseModel):
    """Base model for Commitment with common attributes."""
    role: str


class CommitmentCreate(CommitmentBase):
    """Model for creating a new commitment.
    
    Requires user_id and proposal_id to establish the relationship.
    """
    user_id: uuid.UUID
    proposal_id: uuid.UUID


class CommitmentUpdate(BaseModel):
    """Model for updating an existing commitment. Role is optional."""
    role: Optional[str] = None


class Commitment(CommitmentBase):
    """Response model for a Commitment."""
    id: uuid.UUID
    user_id: uuid.UUID
    proposal_id: uuid.UUID
    commitment_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)