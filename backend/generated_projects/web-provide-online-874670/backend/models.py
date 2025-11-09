from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Base Pydantic model configuration
class Base(BaseModel):
    """
    Base model with ORM mode enabled.
    All other Pydantic models will inherit from this class.
    """
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# User Models
# ---------------------------------------------------------------------------

class UserBase(Base):
    """
    Base schema for a user, containing shared fields.
    """
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    Includes the password field which is required for creation.
    """
    password: str = Field(..., min_length=8)


class UserUpdate(Base):
    """
    Schema for updating an existing user.
    All fields are optional to allow for partial updates.
    """
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    """
    Schema for returning a user in an API response.
    Excludes sensitive information like the hashed password.
    """
    id: UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Product Models
# ---------------------------------------------------------------------------

class ProductBase(Base):
    """
    Base schema for a product, with all common fields.
    """
    name: str = Field(..., max_length=255)
    description: str
    price: float = Field(..., gt=0)
    image_url: str = Field(..., max_length=2048)
    stock_quantity: int = Field(..., ge=0)
    category: str = Field(..., max_length=100)
    tags: List[str] = []


class ProductCreate(ProductBase):
    """
    Schema for creating a new product. Inherits all fields from ProductBase.
    """
    pass


class ProductUpdate(Base):
    """
    Schema for updating an existing product.
    All fields are optional to allow for partial updates.
    """
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    image_url: Optional[str] = Field(None, max_length=2048)
    stock_quantity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None


class ProductResponse(ProductBase):
    """
    Schema for returning a product in an API response.
    Includes the database-generated ID.
    """
    id: int


# ---------------------------------------------------------------------------
# Cart Models
# ---------------------------------------------------------------------------

class CartBase(Base):
    """
    Base schema for a shopping cart.
    Represents the link between a user/session and their cart.
    """
    user_id: Optional[UUID] = None
    session_id: Optional[str] = None


class CartCreate(CartBase):
    """
    Schema for creating a new cart.
    The backend will typically handle ID and timestamps.
    """
    pass


class CartUpdate(Base):
    """
    Schema for updating a cart.
    For example, assigning a guest cart (session_id) to a logged-in user (user_id).
    """
    user_id: Optional[UUID] = None
    session_id: Optional[str] = None


class CartResponse(CartBase):
    """
    Schema for returning a cart in an API response.
    Includes all database-managed fields.
    """
    id: UUID
    created_at: datetime
    updated_at: datetime
