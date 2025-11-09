from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Enums ---

class ProductCategory(str, Enum):
    """Enum for product categories."""
    GROCERY = "Grocery"
    ELECTRONICS = "Electronics"


class OrderStatus(str, Enum):
    """Enum for order statuses."""
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


# --- Product Models ---

class ProductBase(BaseModel):
    """Base model for a product, containing common attributes."""
    sku: str
    name: str
    description: str
    price: float
    stock_quantity: int
    category: ProductCategory
    image_urls: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any]


class ProductCreate(ProductBase):
    """Model for creating a new product. Inherits all fields from ProductBase."""
    pass


class ProductUpdate(BaseModel):
    """Model for updating an existing product. All fields are optional."""
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    category: Optional[ProductCategory] = None
    image_urls: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None


class Product(ProductBase):
    """Response model for a product, including the database-generated ID."""
    id: int

    # Pydantic v2 config for ORM mode and example data
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 205,
                    "sku": "SNY-HDPH-XM5",
                    "name": "Sony WH-1000XM5 Headphones",
                    "description": "Industry-leading noise canceling headphones with a new design.",
                    "price": 399.99,
                    "stock_quantity": 50,
                    "category": "Electronics",
                    "image_urls": [
                        "https://example.com/images/sony-xm5-1.jpg",
                        "https://example.com/images/sony-xm5-2.jpg"
                    ],
                    "attributes": {
                        "brand": "Sony",
                        "color": "Black",
                        "noise_cancelling": True
                    }
                }
            ]
        }
    )


# --- User Models ---

class UserBase(BaseModel):
    """Base model for a user, containing common attributes."""
    email: str
    full_name: str
    default_address: Dict[str, Any]


class UserCreate(UserBase):
    """Model for creating a new user. Includes password for creation."""
    password: str


class UserUpdate(BaseModel):
    """Model for updating an existing user. All fields are optional."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    default_address: Optional[Dict[str, Any]] = None
    password: Optional[str] = None


class User(UserBase):
    """Response model for a user, excluding sensitive data like password."""
    id: int
    hashed_password: str
    created_at: datetime

    # Pydantic v2 config for ORM mode and example data
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "email": "customer@example.com",
                    "full_name": "Jane Doe",
                    "default_address": {
                        "street": "123 Main St",
                        "city": "Anytown",
                        "state": "CA",
                        "zip_code": "12345"
                    },
                    "created_at": "2023-10-27T10:00:00Z",
                    "hashed_password": "supersecret-and-hashed-password"
                }
            ]
        }
    )


# --- Order Models ---

class OrderBase(BaseModel):
    """Base model for an order, containing common attributes."""
    user_id: int
    status: OrderStatus
    total_amount: float
    shipping_address: Dict[str, Any]
    delivery_slot: Optional[datetime] = None
    tracking_number: Optional[str] = None


class OrderCreate(OrderBase):
    """Model for creating a new order."""
    # Status can be defaulted on creation
    status: OrderStatus = OrderStatus.PENDING


class OrderUpdate(BaseModel):
    """Model for updating an existing order. All fields are optional."""
    user_id: Optional[int] = None
    status: Optional[OrderStatus] = None
    total_amount: Optional[float] = None
    shipping_address: Optional[Dict[str, Any]] = None
    delivery_slot: Optional[datetime] = None
    tracking_number: Optional[str] = None


class Order(OrderBase):
    """Response model for an order, including database-generated fields."""
    id: int
    created_at: datetime

    # Pydantic v2 config for ORM mode and example data
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1023,
                    "user_id": 1,
                    "status": "shipped",
                    "total_amount": 425.50,
                    "created_at": "2023-10-26T15:30:00Z",
                    "shipping_address": {
                        "recipient_name": "Jane Doe",
                        "street": "123 Main St",
                        "city": "Anytown",
                        "state": "CA",
                        "zip_code": "12345"
                    },
                    "delivery_slot": None,
                    "tracking_number": "1Z999AA10123456784"
                }
            ]
        }
    )