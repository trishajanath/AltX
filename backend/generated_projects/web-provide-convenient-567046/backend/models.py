from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, Json


# region User Models

class UserBase(BaseModel):
    """Base model for User, containing shared fields."""
    email: str = Field(..., example="user@example.com")
    full_name: str = Field(..., min_length=2, max_length=100, example="John Doe")
    default_address: Optional[Json[Any]] = Field(None, example='{"street": "123 Main St", "city": "Anytown"}')


class UserCreate(UserBase):
    """Model for creating a new user."""
    hashed_password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Model for updating an existing user. All fields are optional."""
    email: Optional[str] = Field(None, example="user@example.com")
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, example="John Doe")
    hashed_password: Optional[str] = Field(None, min_length=8)
    default_address: Optional[Json[Any]] = Field(None, example='{"street": "123 Main St", "city": "Anytown"}')


class UserResponse(UserBase):
    """Model for returning a user in API responses (password excluded)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# endregion


# region Product Models

class ProductBase(BaseModel):
    """Base model for Product, containing shared fields."""
    sku: str = Field(..., max_length=50, example="TSHIRT-BLK-LG")
    name: str = Field(..., max_length=200, example="Black T-Shirt")
    description: str = Field(..., example="A comfortable, high-quality black t-shirt.")
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, example=19.99)
    image_url: str = Field(..., example="https://example.com/images/tshirt-black.jpg")
    stock_quantity: int = Field(..., ge=0, example=100)
    category: str = Field(..., max_length=100, example="Apparel")
    tags: List[str] = Field([], example=["clothing", "summer", "casual"])


class ProductCreate(ProductBase):
    """Model for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Model for updating an existing product. All fields are optional."""
    sku: Optional[str] = Field(None, max_length=50, example="TSHIRT-BLK-LG")
    name: Optional[str] = Field(None, max_length=200, example="Black T-Shirt")
    description: Optional[str] = Field(None, example="A comfortable, high-quality black t-shirt.")
    price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2, example=21.50)
    image_url: Optional[str] = Field(None, example="https://example.com/images/tshirt-black-new.jpg")
    stock_quantity: Optional[int] = Field(None, ge=0, example=95)
    category: Optional[str] = Field(None, max_length=100, example="Apparel")
    tags: Optional[List[str]] = Field(None, example=["clothing", "sale"])


class ProductResponse(ProductBase):
    """Model for returning a product in API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int


# endregion


# region Order Models

class OrderBase(BaseModel):
    """Base model for Order, containing shared fields."""
    user_id: UUID
    status: str = Field("pending", max_length=50, example="pending")
    delivery_slot_start: datetime
    delivery_slot_end: datetime
    shipping_address: Json[Any] = Field(..., example='{"street": "123 Main St", "city": "Anytown", "zip": "12345"}')


class OrderCreate(OrderBase):
    """
    Model for creating a new order.
    In a real application, this would likely contain a list of product IDs and quantities
    instead of a pre-calculated total_price.
    """
    pass


class OrderUpdate(BaseModel):
    """Model for updating an existing order. All fields are optional."""
    status: Optional[str] = Field(None, max_length=50, example="shipped")
    delivery_slot_start: Optional[datetime] = None
    delivery_slot_end: Optional[datetime] = None
    shipping_address: Optional[Json[Any]] = Field(None, example='{"street": "456 Oak Ave", "city": "Anytown", "zip": "12345"}')


class OrderResponse(OrderBase):
    """Model for returning an order in API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    total_price: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2, example=129.45)
    created_at: datetime

# endregion