import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    model_validator,
)

# A base model with from_attributes=True for ORM integration
class BaseSchema(BaseModel):
    """Base Pydantic schema with ORM mode (from_attributes) enabled."""
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# User Models
# =============================================================================

class UserBase(BaseSchema):
    """Base schema for User, containing shared fields."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    default_address: dict[str, Any] | None = None
    dietary_preferences: list[str] = Field(default_factory=list)


class UserCreate(UserBase):
    """Schema for creating a new User. Includes password for creation."""
    password: str = Field(..., min_length=8, description="User's password")


class UserUpdate(BaseSchema):
    """
    Schema for updating an existing User. All fields are optional.
    Inherits from BaseSchema directly to make all fields optional.
    """
    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=2, max_length=100)
    default_address: dict[str, Any] | None = None
    dietary_preferences: list[str] | None = None
    password: str | None = Field(None, min_length=8, description="New password")


class UserResponse(UserBase):
    """
    Schema for returning a User in an API response.
    Excludes sensitive data like hashed_password.
    """
    id: uuid.UUID
    created_at: datetime


# =============================================================================
# Product Models
# =============================================================================

class ProductBase(BaseSchema):
    """Base schema for Product, containing shared fields."""
    sku: str = Field(..., max_length=50, description="Stock Keeping Unit")
    name: str = Field(..., max_length=200)
    description: str
    price: float = Field(..., gt=0, description="Price must be positive")
    image_url: HttpUrl
    stock_quantity: int = Field(..., ge=0, description="Stock cannot be negative")
    category: str = Field(..., max_length=100)
    tags: list[str] = Field(default_factory=list)


class ProductCreate(ProductBase):
    """Schema for creating a new Product."""
    pass


class ProductUpdate(BaseSchema):
    """Schema for updating an existing Product. All fields are optional."""
    sku: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    price: float | None = Field(None, gt=0)
    image_url: HttpUrl | None = None
    stock_quantity: int | None = Field(None, ge=0)
    category: str | None = Field(None, max_length=100)
    tags: list[str] | None = None


class ProductResponse(ProductBase):
    """Schema for returning a Product in an API response."""
    id: uuid.UUID


# =============================================================================
# Order and OrderItem Models
# =============================================================================

# OrderItem is a component of Order. We define its schemas first.
# The prompt specifies `list[OrderItem]`, which we interpret as a response model.
# A separate `OrderItemCreate` is needed for creating orders.

class OrderItemCreate(BaseSchema):
    """Schema for an item when creating an order."""
    product_id: uuid.UUID
    quantity: int = Field(..., gt=0, description="Quantity must be positive")


class OrderItem(BaseSchema):
    """Schema for an item within an order response."""
    product_id: uuid.UUID
    quantity: int
    # In a real app, you would likely include the price at the time of order
    # and potentially nested product details.
    # price_at_order: float
    # product: ProductResponse


class OrderBase(BaseSchema):
    """Base schema for Order, containing shared fields."""
    status: str = Field("pending", max_length=50)
    delivery_slot_start: datetime
    delivery_slot_end: datetime

    @model_validator(mode='after')
    def check_delivery_slots(self) -> 'OrderBase':
        """Ensures the delivery end time is after the start time."""
        if self.delivery_slot_start >= self.delivery_slot_end:
            raise ValueError('delivery_slot_end must be after delivery_slot_start')
        return self


class OrderCreate(OrderBase):
    """Schema for creating a new Order."""
    user_id: uuid.UUID
    items: list[OrderItemCreate]


class OrderUpdate(BaseSchema):
    """
    Schema for updating an existing Order.
    Typically, only status or delivery times are updatable.
    """
    status: str | None = Field(None, max_length=50)
    delivery_slot_start: datetime | None = None
    delivery_slot_end: datetime | None = None

    @model_validator(mode='after')
    def check_delivery_slots(self) -> 'OrderUpdate':
        """Ensures the delivery end time is after the start time if both are provided."""
        if self.delivery_slot_start and self.delivery_slot_end:
            if self.delivery_slot_start >= self.delivery_slot_end:
                raise ValueError('delivery_slot_end must be after delivery_slot_start')
        return self


class OrderResponse(OrderBase):
    """Schema for returning an Order in an API response."""
    id: uuid.UUID
    user_id: uuid.UUID
    total_price: float
    created_at: datetime
    items: list[OrderItem]