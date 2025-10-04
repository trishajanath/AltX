import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# ======================================================================================
# Base Configuration
# ======================================================================================

class BaseSchema(BaseModel):
    """
    Base Pydantic schema with from_attributes=True for ORM mode.
    All response models will inherit from this.
    """
    model_config = ConfigDict(from_attributes=True)


# ======================================================================================
# Product Models
# ======================================================================================

class ProductBase(BaseModel):
    """Shared properties for a Product."""
    sku: str = Field(..., max_length=50, description="Stock Keeping Unit")
    name: str = Field(..., max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Detailed product description")
    image_url: Optional[HttpUrl] = Field(None, description="URL for the product image")
    price: float = Field(..., gt=0, description="Product price, must be positive")
    category: str = Field(..., max_length=100, description="Product category")
    tags: Optional[List[str]] = Field(None, description="List of tags for the product")
    nutritional_info_json: Optional[Dict[str, Any]] = Field(
        None, description="Nutritional information in JSON format"
    )


class ProductCreate(ProductBase):
    """Properties to receive via API on creation."""
    pass


class ProductUpdate(BaseModel):
    """Properties to receive via API on update, all optional."""
    sku: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    nutritional_info_json: Optional[Dict[str, Any]] = None


class ProductResponse(ProductBase, BaseSchema):
    """Properties to return to client, including database-generated id."""
    id: int


# ======================================================================================
# StoreInventory Models
# ======================================================================================

class StoreInventoryBase(BaseModel):
    """Shared properties for StoreInventory."""
    product_id: int = Field(..., description="Foreign key to the Product")
    store_id: int = Field(..., description="Foreign key to the Store")
    stock_level: int = Field(..., ge=0, description="Current stock level, cannot be negative")


class StoreInventoryCreate(StoreInventoryBase):
    """Properties to receive via API on creation."""
    pass


class StoreInventoryUpdate(BaseModel):
    """Properties to receive via API on update, all optional."""
    stock_level: Optional[int] = Field(None, ge=0, description="Updated stock level")


class StoreInventoryResponse(StoreInventoryBase, BaseSchema):
    """Properties to return to client."""
    id: int
    last_updated_at: datetime


# ======================================================================================
# Order Models
# ======================================================================================

class OrderBase(BaseModel):
    """Shared properties for an Order."""
    user_id: int = Field(..., description="Foreign key to the User who placed the order")
    store_id: int = Field(..., description="Foreign key to the Store for the order")
    rider_id: Optional[int] = Field(None, description="Foreign key to the Rider assigned to the order")
    status: str = Field("pending", max_length=50, description="Current status of the order")
    total_price: float = Field(..., gt=0, description="Total price of the order")
    delivery_address_json: Dict[str, Any] = Field(
        ..., description="Delivery address in JSON format"
    )
    estimated_delivery_at: Optional[datetime] = Field(
        None, description="Estimated time of delivery"
    )


class OrderCreate(OrderBase):
    """Properties to receive via API on creation."""
    # You might want to exclude some fields from creation, e.g., status
    # For this example, we'll allow them to be set.
    pass


class OrderUpdate(BaseModel):
    """Properties to receive via API on update, all optional."""
    rider_id: Optional[int] = None
    status: Optional[str] = Field(None, max_length=50)
    estimated_delivery_at: Optional[datetime] = None
    actual_delivery_at: Optional[datetime] = None


class OrderResponse(OrderBase, BaseSchema):
    """Properties to return to client."""
    id: int
    actual_delivery_at: Optional[datetime] = Field(
        None, description="Actual time of delivery"
    )
    created_at: datetime