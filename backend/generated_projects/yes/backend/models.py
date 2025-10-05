from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# A base model with ORM mode enabled
class OrmBase(BaseModel):
    """Base Pydantic model with from_attributes=True for ORM compatibility."""
    model_config = ConfigDict(from_attributes=True)


# ------------------ User Models ------------------

class UserBase(OrmBase):
    """Base model for User, containing common fields."""
    email: str


class UserCreate(UserBase):
    """Model for creating a new user. Expects a password."""
    hashed_password: str


class UserUpdate(OrmBase):
    """Model for updating a user. All fields are optional."""
    email: Optional[str] = None
    hashed_password: Optional[str] = None


class UserResponse(UserBase):
    """Model for returning a user in API responses."""
    id: UUID
    created_at: datetime


# ------------------ Goal Models ------------------

class GoalStatusEnum(str, Enum):
    """Enum for the status of a goal."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class GoalBase(OrmBase):
    """Base model for Goal, containing common fields."""
    title: str
    description: str
    category: str
    target_date: date
    status: GoalStatusEnum = GoalStatusEnum.ACTIVE


class GoalCreate(GoalBase):
    """Model for creating a new goal."""
    user_id: UUID


class GoalUpdate(OrmBase):
    """Model for updating a goal. All fields are optional."""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    target_date: Optional[date] = None
    status: Optional[GoalStatusEnum] = None


class GoalResponse(GoalBase):
    """Model for returning a goal in API responses."""
    id: UUID
    user_id: UUID


# ------------------ Milestone Models ------------------

class MilestoneBase(OrmBase):
    """Base model for Milestone, containing common fields."""
    title: str
    target_date: date


class MilestoneCreate(MilestoneBase):
    """Model for creating a new milestone."""
    goal_id: UUID
    is_completed: bool = False


class MilestoneUpdate(OrmBase):
    """Model for updating a milestone. All fields are optional."""
    title: Optional[str] = None
    is_completed: Optional[bool] = None
    target_date: Optional[date] = None


class MilestoneResponse(MilestoneBase):
    """Model for returning a milestone in API responses."""
    id: UUID
    goal_id: UUID
    is_completed: bool