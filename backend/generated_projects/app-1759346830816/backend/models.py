from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# --- Enums ---

class OrderStatus(str, Enum):
    """Enum for possible order statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# --- Base Schemas (for creation/updates) ---

class UserBase(BaseModel):
    """Base schema for user data."""
    email: EmailStr
    firstName: str = Field(..., min_length=1, max_length=50)
    lastName: str = Field(..., min_length=1, max_length=50)

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    """Schema for updating an existing user. All fields are optional."""
    email: EmailStr | None = None
    firstName: str | None = Field(None, min_length=1, max_length=50)
    lastName: str | None = Field(None, min_length=1, max_length=50)


class ProductBase(BaseModel):
    """Base schema for product data."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str
    price: float = Field(..., gt=0, description="Price must be positive")
    stockQuantity: int = Field(..., ge=0, description="Stock quantity cannot be negative")
    imageUrl: str | None = None
    categoryId: uuid.UUID

class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass

class ProductUpdate(BaseModel):
    """Schema for updating a product. All fields are optional."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    price: float | None = Field(None, gt=0, description="Price must be positive")
    stockQuantity: int | None = Field(None, ge=0, description="Stock quantity cannot be negative")
    imageUrl: str | None = None
    categoryId: uuid.UUID | None = None


class CartItemBase(BaseModel):
    """Base schema for cart item data."""
    productId: uuid.UUID
    quantity: int = Field(..., gt=0, description="Quantity must be at least 1")

class CartItemCreate(CartItemBase):
    """Schema for adding an item to a cart."""
    pass

class CartItemUpdate(BaseModel):
    """Schema for updating a cart item's quantity."""
    quantity: int = Field(..., gt=0, description="Quantity must be at least 1")


class OrderBase(BaseModel):
    """Base schema for order data."""
    shippingAddress: str
    billingAddress: str

class OrderCreate(OrderBase):
    """Schema for creating a new order from a user's cart."""
    pass

class OrderUpdate(BaseModel):
    """Schema for updating an order's status."""
    status: OrderStatus


# --- Response Schemas (for reading data from the API) ---

class Product(ProductBase):
    """Schema for a product as returned by the API."""
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class User(UserBase):
    """Schema for a user as returned by the API (without password)."""
    id: uuid.UUID
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class CartItem(CartItemBase):
    """Schema for a cart item as returned by the API."""
    id: uuid.UUID
    cartId: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class Cart(BaseModel):
    """Schema for a shopping cart as returned by the API."""
    id: uuid.UUID
    userId: uuid.UUID
    createdAt: datetime
    items: list[CartItem] = []
    model_config = ConfigDict(from_attributes=True)


class OrderItem(BaseModel):
    """Schema for an order item as returned by the API."""
    id: uuid.UUID
    orderId: uuid.UUID
    productId: uuid.UUID
    quantity: int
    priceAtPurchase: float
    model_config = ConfigDict(from_attributes=True)


class Order(OrderBase):
    """Schema for an order as returned by the API."""
    id: uuid.UUID
    userId: uuid.UUID
    totalAmount: float
    status: OrderStatus
    createdAt: datetime
    items: list[OrderItem] = []
    model_config = ConfigDict(from_attributes=True)