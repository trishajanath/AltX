from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# --- Base Configuration ---

class Base(BaseModel):
    """
    Base Pydantic model with from_attributes=True.
    This allows the model to be created from ORM objects.
    """
    model_config = ConfigDict(from_attributes=True)


# --- GeoJSON Helper Models ---

class Point(BaseModel):
    """A GeoJSON Point model for representing geographic coordinates."""
    type: Literal["Point"] = "Point"
    coordinates: Tuple[float, float]  # [longitude, latitude]


class Polygon(BaseModel):
    """
    A GeoJSON Polygon model for representing geographic areas.
    The first list of coordinates is the exterior ring, subsequent lists are interior rings (holes).
    """
    type: Literal["Polygon"] = "Polygon"
    coordinates: List[List[Tuple[float, float]]]


# --- Product Models ---

class ProductBase(BaseModel):
    """Base model for a product, containing all common fields."""
    sku: str = Field(..., max_length=50, description="Stock Keeping Unit")
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    imageUrl: Optional[HttpUrl] = Field(None, description="URL for the product image")
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, description="Price of the product")
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = Field(None, description="A list of tags for product filtering")
    unitOfMeasure: str = Field(
        ...,
        max_length=20,
        description="Unit of measure (e.g., 'each', '100g', 'liter')"
    )


class ProductCreate(ProductBase):
    """Model for creating a new product. Inherits all fields from ProductBase."""
    pass


class ProductUpdate(BaseModel):
    """
    Model for updating an existing product.
    All fields are optional to allow for partial updates (PATCH).
    """
    sku: Optional[str] = Field(None, max_length=50, description="Stock Keeping Unit")
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    imageUrl: Optional[HttpUrl] = Field(None, description="URL for the product image")
    price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = Field(None)
    unitOfMeasure: Optional[str] = Field(None, max_length=20)


class Product(ProductBase, Base):
    """
    Response model for a product.
    Includes database-generated fields like 'id'.
    """
    id: UUID


# --- DarkStore Models ---

class DarkStoreBase(BaseModel):
    """Base model for a dark store, containing all common fields."""
    name: str = Field(..., max_length=255)
    address: str
    location: Point = Field(..., description="GeoJSON Point for the store's exact location")
    coverageArea: Polygon = Field(..., description="GeoJSON Polygon representing the delivery coverage area")
    operatingHours: str = Field(..., description="Human-readable operating hours (e.g., 'Mon-Sat 9:00-21:00')")


class DarkStoreCreate(DarkStoreBase):
    """Model for creating a new dark store."""
    pass


class DarkStoreUpdate(BaseModel):
    """
    Model for updating an existing dark store.
    All fields are optional.
    """
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    location: Optional[Point] = Field(None)
    coverageArea: Optional[Polygon] = Field(None)
    operatingHours: Optional[str] = Field(None)


class DarkStore(DarkStoreBase, Base):
    """Response model for a dark store, including the database-generated 'id'."""
    id: UUID


# --- Inventory Models ---

class InventoryBase(BaseModel):
    """Base model for an inventory record."""
    productId: UUID = Field(..., description="Foreign key to the Product")
    darkStoreId: UUID = Field(..., description="Foreign key to the DarkStore")
    stockLevel: int = Field(..., ge=0, description="Current stock level of the product")
    isAvailable: bool = Field(True, description="Whether the product is available for sale")


class InventoryCreate(InventoryBase):
    """Model for creating a new inventory record."""
    pass


class InventoryUpdate(BaseModel):
    """
    Model for updating an inventory record.
    Foreign keys are typically not updatable, so they are excluded.
    """
    stockLevel: Optional[int] = Field(None, ge=0)
    isAvailable: Optional[bool] = None


class Inventory(InventoryBase, Base):
    """
    Response model for an inventory record.
    Includes database-generated fields like 'id' and 'lastUpdatedAt'.
    """
    id: UUID
    lastUpdatedAt: datetime