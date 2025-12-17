from datetime import datetime
from uuid import UUID
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, EmailStr


# =============================================================================
# Base Schema for ORM compatibility
# =============================================================================

class BaseSchema(BaseModel):
    """
    Base Pydantic model that includes a ConfigDict to enable ORM mode.
    All response models will inherit from this to map SQLAlchemy objects.
    """
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# User Models
# =============================================================================

# --- User: Base ---
# Shared properties, used as a base for other user-related schemas.
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)


# --- User: Create ---
# Properties required to create a new user. Includes the password.
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password")


# --- User: Update ---
# Properties that can be updated. All fields are optional.
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=8)


# --- User: Response ---
# Properties to be returned by the API. Inherits from BaseSchema for ORM mapping.
# Excludes sensitive information like hashed_password.
class User(UserBase, BaseSchema):
    id: UUID
    created_at: datetime


# =============================================================================
# Product Models
# =============================================================================

# --- Product: Base ---
# Shared properties for a product.
class ProductBase(BaseModel):
    sku: str = Field(..., max_length=50, description="Stock Keeping Unit")
    name: str = Field(..., max_length=200)
    description: str
    price: float = Field(..., gt=0, description="Price must be greater than zero")
    image_url: str = Field(..., max_length=2048)
    category: str = Field(..., max_length=100)
    stock_quantity: int = Field(..., ge=0, description="Stock quantity cannot be negative")
    dietary_tags: List[str] = []

    # Add example data for OpenAPI documentation
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sku": "ORG-AVO-001",
                "name": "Organic Hass Avocado",
                "description": "A creamy and delicious organic Hass avocado, perfect for toast or guacamole.",
                "price": 2.5,
                "image_url": "https://example.com/images/organic-avocado.jpg",
                "category": "Produce",
                "stock_quantity": 250,
                "dietary_tags": ["organic", "vegan", "gluten-free"]
            }
        }
    )


# --- Product: Create ---
# Properties required to create a new product.
class ProductCreate(ProductBase):
    pass


# --- Product: Update ---
# Properties that can be updated on a product. All fields are optional.
class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    image_url: Optional[str] = Field(None, max_length=2048)
    category: Optional[str] = Field(None, max_length=100)
    stock_quantity: Optional[int] = Field(None, ge=0)
    dietary_tags: Optional[List[str]] = None


# --- Product: Response ---
# Properties to be returned by the API for a product.
class Product(ProductBase, BaseSchema):
    id: UUID


# =============================================================================
# CartItem Models
# =============================================================================

# --- CartItem: Base ---
# Shared properties for a cart item.
class CartItemBase(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0, description="Quantity must be a positive integer")


# --- CartItem: Create ---
# Properties required to create a new cart item.
# In a real app, user_id would likely come from the authenticated user context.
class CartItemCreate(CartItemBase):
    user_id: UUID


# --- CartItem: Update ---
# Properties that can be updated. Typically, only the quantity is updatable.
class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity must be a positive integer")


# --- CartItem: Response ---
# Properties to be returned by the API for a cart item.
class CartItem(CartItemBase, BaseSchema):
    id: UUID
    user_id: UUID
    added_at: datetime
