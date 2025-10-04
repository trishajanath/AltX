from datetime import datetime
from typing import List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

# ==============================================================================
# Product Models
# ==============================================================================

class ProductBase(BaseModel):
    """Base model for a product, containing shared attributes."""
    sku: str = Field(..., max_length=100, description="Stock Keeping Unit for the product.")
    name: str = Field(..., max_length=255, description="Name of the product.")
    description: Optional[str] = Field(None, description="Detailed description of the product.")
    price: float = Field(..., gt=0, description="Price of the product. Must be greater than zero.")
    image_url: Optional[HttpUrl] = Field(None, description="URL of the product's image.")
    category: Optional[str] = Field(None, max_length=100, description="Category the product belongs to.")
    tags: List[str] = Field(default_factory=list, description="A list of tags for product classification.")
    unit_of_measure: Optional[str] = Field(None, max_length=50, description="Unit of measure (e.g., 'kg', 'piece', 'liter').")


class ProductCreate(ProductBase):
    """Model for creating a new product. Inherits all fields from ProductBase."""
    pass


class ProductUpdate(BaseModel):
    """
    Model for updating an existing product. All fields are optional to allow
    for partial updates (PATCH requests).
    """
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit for the product.")
    name: Optional[str] = Field(None, max_length=255, description="Name of the product.")
    description: Optional[str] = Field(None, description="Detailed description of the product.")
    price: Optional[float] = Field(None, gt=0, description="Price of the product. Must be greater than zero.")
    image_url: Optional[HttpUrl] = Field(None, description="URL of the product's image.")
    category: Optional[str] = Field(None, max_length=100, description="Category the product belongs to.")
    tags: Optional[List[str]] = Field(None, description="A list of tags for product classification.")
    unit_of_measure: Optional[str] = Field(None, max_length=50, description="Unit of measure (e.g., 'kg', 'piece', 'liter').")


class Product(ProductBase):
    """
    Response model for a product. Includes database-generated fields like 'id'
    and enables ORM mode for mapping to database objects.
    """
    id: int = Field(..., description="Unique identifier for the product.")

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# DarkStore Models
# ==============================================================================

class DarkStoreBase(BaseModel):
    """Base model for a dark store, containing shared attributes."""
    name: str = Field(..., max_length=255, description="The name of the dark store.")
    address: str = Field(..., description="The physical address of the dark store.")
    # A simple polygon is a list of points, where each point is [lon, lat]
    coverage_area_polygon: Optional[List[Tuple[float, float]]] = Field(None, description="A list of [lon, lat] tuples defining the delivery coverage area.")
    # A single point for the store's location [lon, lat]
    location_coords: Tuple[float, float] = Field(..., description="The geographic coordinates [longitude, latitude] of the store.")
    is_active: bool = Field(True, description="Indicates if the dark store is currently operational.")


class DarkStoreCreate(DarkStoreBase):
    """Model for creating a new dark store."""
    pass


class DarkStoreUpdate(BaseModel):
    """Model for updating an existing dark store. All fields are optional."""
    name: Optional[str] = Field(None, max_length=255, description="The name of the dark store.")
    address: Optional[str] = Field(None, description="The physical address of the dark store.")
    coverage_area_polygon: Optional[List[Tuple[float, float]]] = Field(None, description="A list of [lon, lat] tuples defining the delivery coverage area.")
    location_coords: Optional[Tuple[float, float]] = Field(None, description="The geographic coordinates [longitude, latitude] of the store.")
    is_active: Optional[bool] = Field(None, description="Indicates if the dark store is currently operational.")


class DarkStore(DarkStoreBase):
    """Response model for a dark store, including the 'id' field."""
    id: int = Field(..., description="Unique identifier for the dark store.")

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# StoreInventory Models
# ==============================================================================

class StoreInventoryBase(BaseModel):
    """Base model for store inventory, linking products and dark stores."""
    product_id: int = Field(..., description="Foreign key referencing the product.")
    dark_store_id: int = Field(..., description="Foreign key referencing the dark store.")
    stock_level: int = Field(..., ge=0, description="The current stock level of the product at this store. Cannot be negative.")
    is_available: bool = Field(True, description="Indicates if the product is available for purchase from this store.")


class StoreInventoryCreate(StoreInventoryBase):
    """Model for creating a new inventory record."""
    pass


class StoreInventoryUpdate(BaseModel):
    """
    Model for updating an inventory record. Typically only stock level and
    availability are updated.
    """
    stock_level: Optional[int] = Field(None, ge=0, description="The new stock level. Cannot be negative.")
    is_available: Optional[bool] = Field(None, description="The new availability status.")


class StoreInventory(StoreInventoryBase):
    """
    Response model for a store inventory record, including 'id' and 'last_updated_at'.
    """
    id: int = Field(..., description="Unique identifier for the inventory record.")
    last_updated_at: datetime = Field(..., description="The timestamp of the last update to this record.")

    model_config = ConfigDict(from_attributes=True)