from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- User Models ---

class UserBase(BaseModel):
    """Shared user properties."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Properties to receive via API on user creation."""
    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(BaseModel):
    """Properties to receive via API on user update."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, description="New user password")


class UserResponse(UserBase):
    """Properties to return to client."""
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """Properties stored in DB, including hashed password."""
    password_hash: str


# --- Product Models ---

class ProductBase(BaseModel):
    """Shared product properties."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="The price must be greater than zero")
    stock_quantity: int = Field(..., ge=0, description="Stock quantity cannot be negative")
    images_json: Optional[List[str]] = Field(None, description="A list of image URLs")
    specs_json: Optional[Dict[str, Any]] = Field(None, description="A dictionary of product specifications")


class ProductCreate(ProductBase):
    """Properties to receive via API on product creation."""
    pass


class ProductUpdate(BaseModel):
    """Properties to receive via API on product update."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0, description="The price must be greater than zero")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity cannot be negative")
    images_json: Optional[List[str]] = Field(None, description="A list of image URLs")
    specs_json: Optional[Dict[str, Any]] = Field(None, description="A dictionary of product specifications")


class ProductResponse(ProductBase):
    """Properties to return to client, including the database ID."""
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Order Models ---

class OrderStatus(str, Enum):
    """Enum for possible order statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderBase(BaseModel):
    """Shared order properties."""
    user_id: int
    total_amount: float = Field(..., gt=0)
    status: OrderStatus = OrderStatus.PENDING
    shipping_address: str


class OrderCreate(OrderBase):
    """Properties to receive via API on order creation."""
    pass


class OrderUpdate(BaseModel):
    """Properties to receive via API on order update."""
    # Typically, only status and shipping address might be updatable.
    status: Optional[OrderStatus] = None
    shipping_address: Optional[str] = None


class OrderResponse(OrderBase):
    """Properties to return to client, including database-generated fields."""
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)