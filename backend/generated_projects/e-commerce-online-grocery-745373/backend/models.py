import enum
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


# ===============================================================================
# User Models
# ===============================================================================

class UserBase(BaseModel):
    """Base model for User, contains shared fields."""
    email: EmailStr
    full_name: str | None = None
    default_address: str | None = None


class UserCreate(UserBase):
    """Model for creating a new user. Requires a password."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """
    Model for updating a user. All fields are optional.
    A user can update their email, password, full name, or default address.
    """
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8)
    full_name: str | None = None
    default_address: str | None = None


class UserResponse(UserBase):
    """
    Model for returning user data in API responses.
    Excludes sensitive information like the password.
    Includes database-generated fields like id and created_at.
    """
    id: int
    created_at: datetime

    # Pydantic V2 config to allow mapping from ORM models
    model_config = ConfigDict(from_attributes=True)


# ===============================================================================
# Product Models
# ===============================================================================

class ProductUnit(str, enum.Enum):
    """Enum for product units."""
    LB = "lb"
    EACH = "each"
    OZ = "oz"
    KG = "kg"
    G = "g"


class ProductBase(BaseModel):
    """Base model for Product, contains shared fields."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    unit: ProductUnit = Field(..., description="e.g. 'lb', 'each', 'oz'")
    category: str = Field(..., min_length=1, max_length=50)
    image_url: HttpUrl | None = None
    stock_quantity: int = Field(..., ge=0)
    is_on_sale: bool = False


class ProductCreate(ProductBase):
    """Model for creating a new product. Inherits all fields from ProductBase."""
    pass


class ProductUpdate(BaseModel):
    """
    Model for updating a product. All fields are optional.
    Allows partial updates to a product's details.
    """
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    price: Decimal | None = Field(None, gt=0, decimal_places=2)
    unit: ProductUnit | None = None
    category: str | None = Field(None, min_length=1, max_length=50)
    image_url: HttpUrl | None = None
    stock_quantity: int | None = Field(None, ge=0)
    is_on_sale: bool | None = None


class ProductResponse(ProductBase):
    """
    Model for returning product data in API responses.
    Includes the database-generated product ID.
    """
    id: int

    # Pydantic V2 config to allow mapping from ORM models
    model_config = ConfigDict(from_attributes=True)


# ===============================================================================
# Order Models
# ===============================================================================

class OrderStatus(str, enum.Enum):
    """Enum for order statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderBase(BaseModel):
    """Base model for Order, contains fields provided upon creation."""
    user_id: int
    delivery_address: str
    delivery_slot_start: datetime
    delivery_slot_end: datetime


class OrderCreate(OrderBase):
    """
    Model for creating a new order.
    Status and total_price are typically set by the backend, not the client.
    This model might also include a list of order items in a real application.
    """
    pass


class OrderUpdate(BaseModel):
    """
    Model for updating an order. All fields are optional.
    Typically used by admins to update the order status.
    """
    status: OrderStatus | None = None
    delivery_address: str | None = None
    delivery_slot_start: datetime | None = None
    delivery_slot_end: datetime | None = None


class OrderResponse(OrderBase):
    """
    Model for returning order data in API responses.
    Includes all database-managed fields like id, status, total_price, and created_at.
    """
    id: int
    status: OrderStatus
    total_price: Decimal = Field(..., decimal_places=2)
    created_at: datetime

    # Pydantic V2 config to allow mapping from ORM models
    model_config = ConfigDict(from_attributes=True)
