from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# Base model with shared configuration for ORM mapping
class ModelBase(BaseModel):
    """A base model with from_attributes=True for ORM compatibility."""
    model_config = ConfigDict(from_attributes=True)


# ===================================================================
# ProductInventory Models
# ===================================================================

class ProductInventoryBase(BaseModel):
    """Base model for product inventory, containing shared fields."""
    sku: str = Field(..., max_length=100, description="Stock Keeping Unit")
    dark_store_id: int = Field(..., description="Foreign key to the DarkStore")
    name: str = Field(..., max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Detailed product description")
    image_url: Optional[HttpUrl] = Field(None, description="URL for the product image")
    price: float = Field(..., gt=0, description="Price of the product")
    stock_quantity: int = Field(..., ge=0, description="Available stock quantity")
    is_available: bool = Field(True, description="Whether the product is available for purchase")
    category: str = Field(..., max_length=100, description="Product category")
    tags: Optional[List[str]] = Field(None, description="List of tags for the product")


class ProductInventoryCreate(ProductInventoryBase):
    """Model for creating a new product inventory record. Inherits all fields from Base."""
    pass


class ProductInventoryUpdate(BaseModel):
    """
    Model for updating an existing product inventory record.
    All fields are optional.
    """
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit")
    dark_store_id: Optional[int] = Field(None, description="Foreign key to the DarkStore")
    name: Optional[str] = Field(None, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Detailed product description")
    image_url: Optional[HttpUrl] = Field(None, description="URL for the product image")
    price: Optional[float] = Field(None, gt=0, description="Price of the product")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Available stock quantity")
    is_available: Optional[bool] = Field(None, description="Whether the product is available for purchase")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    tags: Optional[List[str]] = Field(None, description="List of tags for the product")


class ProductInventory(ProductInventoryBase, ModelBase):
    """Response model for product inventory, including the database-generated ID."""
    id: int = Field(..., description="Primary key")


# ===================================================================
# Order Models
# ===================================================================

class OrderBase(BaseModel):
    """Base model for an order, containing fields provided upon creation."""
    user_id: int = Field(..., description="Foreign key to the User")
    dark_store_id: int = Field(..., description="Foreign key to the DarkStore")
    rider_id: Optional[int] = Field(None, description="Foreign key to the Rider")
    status: str = Field("pending", max_length=50, description="Current status of the order (e.g., pending, dispatched, delivered)")
    items_snapshot: List[Dict[str, Any]] = Field(..., description="A JSON snapshot of the items at the time of order")
    subtotal: float = Field(..., ge=0, description="The total price of items before fees")
    delivery_fee: float = Field(..., ge=0, description="The fee for delivery")
    total_price: float = Field(..., ge=0, description="The final price including all fees")
    delivery_address: str = Field(..., description="The full delivery address as a string")
    delivery_location_coordinates: Dict[str, float] = Field(..., description="Geo-coordinates for delivery, e.g., {'lat': 40.7128, 'lon': -74.0060}")


class OrderCreate(OrderBase):
    """Model for creating a new order. Inherits all fields from Base."""
    pass


class OrderUpdate(BaseModel):
    """
    Model for updating an existing order.
    Typically, only a subset of fields like status or rider_id can be updated.
    """
    rider_id: Optional[int] = Field(None, description="Foreign key to the Rider")
    status: Optional[str] = Field(None, max_length=50, description="Updated status of the order")
    dispatched_at: Optional[datetime] = Field(None, description="Timestamp when the order was dispatched")
    delivered_at: Optional[datetime] = Field(None, description="Timestamp when the order was delivered")


class Order(OrderBase, ModelBase):
    """Response model for an order, including all database-generated fields."""
    id: int = Field(..., description="Primary key")
    created_at: datetime = Field(..., description="Timestamp when the order was created")
    dispatched_at: Optional[datetime] = Field(None, description="Timestamp when the order was dispatched")
    delivered_at: Optional[datetime] = Field(None, description="Timestamp when the order was delivered")


# ===================================================================
# DarkStore Models
# ===================================================================

class DarkStoreBase(BaseModel):
    """Base model for a dark store, containing its core attributes."""
    name: str = Field(..., max_length=255, description="Name of the dark store")
    address: str = Field(..., description="Physical address of the dark store")
    service_area_polygon: Any = Field(..., description="GeoJSON-like polygon defining the service area")
    is_active: bool = Field(True, description="Whether the dark store is currently operational")


class DarkStoreCreate(DarkStoreBase):
    """Model for creating a new dark store. Inherits all fields from Base."""
    pass


class DarkStoreUpdate(BaseModel):
    """
    Model for updating an existing dark store.
    All fields are optional.
    """
    name: Optional[str] = Field(None, max_length=255, description="Name of the dark store")
    address: Optional[str] = Field(None, description="Physical address of the dark store")
    service_area_polygon: Optional[Any] = Field(None, description="GeoJSON-like polygon defining the service area")
    is_active: Optional[bool] = Field(None, description="Whether the dark store is currently operational")


class DarkStore(DarkStoreBase, ModelBase):
    """Response model for a dark store, including the database-generated ID."""
    id: int = Field(..., description="Primary key")