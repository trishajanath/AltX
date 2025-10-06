from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


# Base model configuration for all Pydantic models
class Base(BaseModel):
    """
    Base Pydantic model with ORM mode enabled.
    All other models will inherit from this class.
    """
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# User Models
# ---------------------------------------------------------------------------

class UserBase(Base):
    """
    Base model for User, containing shared fields.
    """
    email: EmailStr
    full_name: str
    default_address: dict[str, Any] | None = None


class UserCreate(UserBase):
    """
    Model for creating a new user.
    Includes the password field which is not stored in this form.
    """
    password: str = Field(..., min_length=8, description="User's password")


class UserUpdate(Base):
    """
    Model for updating an existing user.
    All fields are optional.
    """
    email: EmailStr | None = None
    full_name: str | None = None
    default_address: dict[str, Any] | None = None
    password: str | None = Field(None, min_length=8, description="New password")


class UserResponse(UserBase):
    """
    Model for returning user data in API responses.
    Excludes sensitive information like the password.
    """
    id: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Product Models
# ---------------------------------------------------------------------------

class ProductBase(Base):
    """
    Base model for Product, containing shared fields.
    """
    name: str = Field(..., max_length=255)
    description: str
    price: float = Field(..., gt=0, description="Price must be greater than zero")
    image_url: HttpUrl
    category: str = Field(..., max_length=100)
    stock_quantity: int = Field(..., ge=0, description="Stock cannot be negative")
    unit: str = Field(..., max_length=20, description="e.g., 'each', 'lb', 'kg'")


class ProductCreate(ProductBase):
    """
    Model for creating a new product.
    Inherits all fields from ProductBase.
    """
    pass


class ProductUpdate(Base):
    """
    Model for updating an existing product.
    All fields are optional.
    """
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    price: float | None = Field(None, gt=0, description="Price must be greater than zero")
    image_url: HttpUrl | None = None
    category: str | None = Field(None, max_length=100)
    stock_quantity: int | None = Field(None, ge=0, description="Stock cannot be negative")
    unit: str | None = Field(None, max_length=20, description="e.g., 'each', 'lb', 'kg'")


class ProductResponse(ProductBase):
    """
    Model for returning product data in API responses.
    """
    id: int


# ---------------------------------------------------------------------------
# Order Models
# ---------------------------------------------------------------------------

# Define a type for order status for reusability and clarity
OrderStatus = Literal['pending', 'paid', 'out_for_delivery', 'delivered']


class OrderBase(Base):
    """
    Base model for Order, containing shared fields.
    """
    user_id: int
    delivery_slot_start: datetime
    delivery_address: dict[str, Any]


class OrderCreate(OrderBase):
    """
    Model for creating a new order.
    Status and total_price are typically set by the server logic,
    but total_price is included here assuming it's calculated on the client
    or based on a cart object not detailed here.
    """
    total_price: float = Field(..., gt=0, description="Total price must be positive")


class OrderUpdate(Base):
    """
    Model for updating an existing order.
    Typically, only the status or delivery time might be updatable.
    """
    status: OrderStatus | None = None
    delivery_slot_start: datetime | None = None


class OrderResponse(OrderBase):
    """
    Model for returning order data in API responses.
    """
    id: int
    status: OrderStatus
    total_price: float
    created_at: datetime