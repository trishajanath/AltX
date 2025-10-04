from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl, Field

# --- Enums ---

class OrderStatus(str, Enum):
    """Enumeration for possible order statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# --- User Models ---

class UserBase(BaseModel):
    """Base model for User, containing shared fields."""
    email: EmailStr
    full_name: str | None = None
    address: str | None = None


class UserCreate(UserBase):
    """Model for creating a new user. Expects a plain password."""
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    """Model for updating an existing user. All fields are optional."""
    email: EmailStr | None = None
    full_name: str | None = None
    address: str | None = None
    password: str | None = Field(default=None, min_length=8)


class User(UserBase):
    """Model for API responses representing a user. Excludes sensitive data."""
    id: int
    
    # Pydantic v2 config to allow mapping from ORM models
    model_config = ConfigDict(from_attributes=True)


class UserInDB(User):
    """
    Internal model representing a user as stored in the database.
    Includes the password hash.
    """
    password_hash: str


# --- Product Models ---

class ProductBase(BaseModel):
    """Base model for Product, containing shared fields."""
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    price: float = Field(gt=0, description="Price must be greater than zero")
    stock_quantity: int = Field(ge=0, description="Stock quantity cannot be negative")
    image_url: HttpUrl | None = None


class ProductCreate(ProductBase):
    """Model for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Model for updating an existing product. All fields are optional."""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    price: float | None = Field(default=None, gt=0, description="Price must be greater than zero")
    stock_quantity: int | None = Field(default=None, ge=0, description="Stock quantity cannot be negative")
    image_url: HttpUrl | None = None


class Product(ProductBase):
    """Model for API responses representing a product."""
    id: int
    
    # Pydantic v2 config to allow mapping from ORM models
    model_config = ConfigDict(from_attributes=True)


# --- Order Models ---

class OrderBase(BaseModel):
    """Base model for Order, containing shared fields."""
    delivery_address: str


class OrderCreate(OrderBase):
    """
    Model for creating a new order.
    In a real application, this would likely include a list of product IDs and quantities.
    user_id, status, total_amount, and created_at are expected to be set by the backend.
    """
    pass


class OrderUpdate(BaseModel):
    """Model for updating an existing order. Only status and address are updatable."""
    status: OrderStatus | None = None
    delivery_address: str | None = None


class Order(OrderBase):
    """Model for API responses representing an order."""
    id: int
    user_id: int
    status: OrderStatus
    total_amount: float = Field(gt=0)
    created_at: datetime
    
    # Pydantic v2 config to allow mapping from ORM models
    model_config = ConfigDict(from_attributes=True)