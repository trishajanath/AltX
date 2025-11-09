from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# =============================================================================
# User Models
# =============================================================================

class UserBase(BaseModel):
    """Base model for User with common attributes."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    default_address: Dict[str, Any]
    phone_number: str = Field(..., min_length=10, max_length=20)

    # Pydantic v2 configuration for ORM mode (to work with SQLAlchemy models)
    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    """Model for creating a new user. Expects a plain password."""
    password: str = Field(..., min_length=8, description="User's password")


class UserUpdate(BaseModel):
    """Model for updating an existing user. All fields are optional."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    default_address: Optional[Dict[str, Any]] = None
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)


class UserResponse(UserBase):
    """Model for returning user data to the client. Excludes sensitive data."""
    id: UUID
    created_at: datetime


# This model includes the hashed_password and is used for internal purposes,
# such as reading the full user object from the database.
# It should NOT be used in response models sent to the client.
class UserInDB(UserResponse):
    """Model representing a user as stored in the database."""
    hashed_password: str


# =============================================================================
# Product Models
# =============================================================================

class ProductBase(BaseModel):
    """Base model for Product with common attributes."""
    sku: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str
    price: float = Field(..., gt=0, description="Price must be positive")
    category: str = Field(..., max_length=100)
    brand: str = Field(..., max_length=100)
    image_url: str
    stock_quantity: int = Field(..., ge=0, description="Stock cannot be negative")
    tags: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(ProductBase):
    """Model for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Model for updating an existing product. All fields are optional."""
    sku: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    tags: Optional[List[str]] = None


class ProductResponse(ProductBase):
    """Model for returning product data to the client."""
    id: int


# =============================================================================
# Order Models
# =============================================================================

class OrderBase(BaseModel):
    """Base model for Order with common attributes."""
    user_id: UUID
    status: str = Field("pending", max_length=50)
    delivery_address: Dict[str, Any]
    delivery_slot_start: datetime
    delivery_slot_end: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(OrderBase):
    """
    Model for creating a new order.
    Total price is calculated on the backend, so it's not included here.
    """
    # In a real application, you would likely include the items being ordered
    # e.g., items: List[OrderItemCreate]
    pass


class OrderUpdate(BaseModel):
    """Model for updating an existing order. All fields are optional."""
    status: Optional[str] = Field(None, max_length=50)
    delivery_address: Optional[Dict[str, Any]] = None
    delivery_slot_start: Optional[datetime] = None
    delivery_slot_end: Optional[datetime] = None


class OrderResponse(OrderBase):
    """Model for returning order data to the client."""
    id: UUID
    total_price: float
    created_at: datetime