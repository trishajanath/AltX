import enum
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


# Base model with shared configuration
class SchemaBase(BaseModel):
    """Base Pydantic model with from_attributes enabled."""
    model_config = ConfigDict(from_attributes=True)


# Shared Models & Enums
class Address(BaseModel):
    """Represents a physical address."""
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str


class OrderStatus(str, enum.Enum):
    """Enum for possible order statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# User Models
# --------------------------------------------------------------------------

class UserBase(SchemaBase):
    """Base schema for User, containing shared fields."""
    email: EmailStr
    full_name: str
    default_address: Optional[Address] = None


class UserCreate(UserBase):
    """Schema for creating a new User. Includes password."""
    password: str = Field(..., min_length=8)


class UserUpdate(SchemaBase):
    """Schema for updating an existing User. All fields are optional."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    default_address: Optional[Address] = None


class UserResponse(UserBase):
    """Schema for returning User data in API responses."""
    id: UUID
    created_at: datetime


# Product Models
# --------------------------------------------------------------------------

class ProductBase(SchemaBase):
    """Base schema for Product, containing shared fields."""
    name: str = Field(..., max_length=255)
    description: str
    price: Decimal = Field(..., gt=0, decimal_places=2)
    image_url: HttpUrl
    category: str = Field(..., max_length=100)
    stock_quantity: int = Field(..., ge=0)
    unit: str = Field(..., max_length=20)  # e.g., 'each', 'lb', 'oz'


class ProductCreate(ProductBase):
    """Schema for creating a new Product."""
    pass


class ProductUpdate(SchemaBase):
    """Schema for updating an existing Product. All fields are optional."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    image_url: Optional[HttpUrl] = None
    category: Optional[str] = Field(None, max_length=100)
    stock_quantity: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=20)


class ProductResponse(ProductBase):
    """Schema for returning Product data in API responses."""
    id: UUID


# Order Models
# --------------------------------------------------------------------------

class OrderBase(SchemaBase):
    """Base schema for Order, containing shared fields."""
    status: OrderStatus = OrderStatus.PENDING
    delivery_address: Address
    delivery_slot_start: datetime


class OrderCreate(OrderBase):
    """Schema for creating a new Order."""
    user_id: UUID
    # total_price will likely be calculated on the backend based on cart items
    # It's excluded from create schema to prevent client manipulation.


class OrderUpdate(SchemaBase):
    """Schema for updating an existing Order. All fields are optional."""
    status: Optional[OrderStatus] = None
    delivery_address: Optional[Address] = None
    delivery_slot_start: Optional[datetime] = None


class OrderResponse(OrderBase):
    """Schema for returning Order data in API responses."""
    id: UUID
    user_id: UUID
    total_price: Decimal = Field(..., gt=0, decimal_places=2)
    created_at: datetime