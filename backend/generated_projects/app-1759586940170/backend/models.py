import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# Base model configuration
class Base(BaseModel):
    """Base Pydantic model with ORM mode enabled."""
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Product Models
# =============================================================================

class ProductBase(Base):
    """Base model for a product, containing shared attributes."""
    sku: str = Field(..., description="Stock Keeping Unit", example="SNK-DOR-045")
    name: str = Field(..., min_length=1, max_length=100, example="Spicy Nacho Chips")
    description: Optional[str] = Field(None, max_length=500, example="Extra spicy tortilla chips.")
    image_url: Optional[HttpUrl] = Field(None, example="https://example.com/images/spicy-nacho.jpg")
    price: float = Field(..., gt=0, description="Price of the product in USD.", example=4.99)
    category: str = Field(..., max_length=50, example="Snacks")
    tags: Optional[List[str]] = Field(None, example=["spicy", "chips", "party"])
    unit_of_measure: Optional[str] = Field(None, max_length=20, example="150g bag")


class ProductCreate(ProductBase):
    """Model for creating a new product. All fields are required."""
    pass


class ProductUpdate(Base):
    """Model for updating an existing product. All fields are optional."""
    sku: Optional[str] = Field(None, description="Stock Keeping Unit", example="SNK-DOR-045")
    name: Optional[str] = Field(None, min_length=1, max_length=100, example="Spicy Nacho Chips")
    description: Optional[str] = Field(None, max_length=500, example="Extra spicy tortilla chips.")
    image_url: Optional[HttpUrl] = Field(None, example="https://example.com/images/spicy-nacho.jpg")
    price: Optional[float] = Field(None, gt=0, description="Price of the product in USD.", example=5.49)
    category: Optional[str] = Field(None, max_length=50, example="Snacks")
    tags: Optional[List[str]] = Field(None, example=["spicy", "chips", "party", "new"])
    unit_of_measure: Optional[str] = Field(None, max_length=20, example="150g bag")


class ProductResponse(ProductBase):
    """Model for representing a product in API responses."""
    id: str = Field(..., description="Unique product identifier", example="prod_1a2b3c")


# =============================================================================
# Dark Store Inventory Models
# =============================================================================

class DarkStoreInventoryBase(Base):
    """Base model for dark store inventory."""
    product_id: str = Field(..., description="The ID of the product.", example="prod_1a2b3c")
    dark_store_id: str = Field(..., description="The ID of the dark store.", example="store_nyc_chelsea")
    stock_level: int = Field(..., ge=0, description="Current stock level of the product.", example=75)


class DarkStoreInventoryCreate(DarkStoreInventoryBase):
    """Model for creating a new inventory record."""
    pass


class DarkStoreInventoryUpdate(Base):
    """
    Model for updating an inventory record.
    Typically, only the stock level is updated.
    """
    stock_level: int = Field(..., ge=0, description="The new stock level.", example=50)


class DarkStoreInventoryResponse(DarkStoreInventoryBase):
    """Model for representing inventory in API responses."""
    id: str = Field(..., description="Unique inventory record identifier", example=f"inv_{uuid.uuid4()}")
    last_updated: datetime = Field(..., description="Timestamp of the last inventory update.")


# =============================================================================
# Order Models
# =============================================================================

class OrderItemBase(Base):
    """Base model for an item within an order."""
    product_id: str = Field(..., description="The ID of the product being ordered.", example="prod_1a2b3c")
    quantity: int = Field(..., gt=0, description="Number of units of the product.", example=2)


class OrderItemCreate(OrderItemBase):
    """Model for an item when creating an order."""
    pass


class OrderItemResponse(OrderItemBase):
    """Model for an item in an order response, including the price at time of purchase."""
    price: float = Field(..., description="Price of the single item at the time of order.", example=4.99)


class OrderBase(Base):
    """Base model for an order."""
    dark_store_id: str = Field(..., description="The ID of the dark store fulfilling the order.", example="store_nyc_chelsea")
    delivery_address: str = Field(..., description="Full delivery address for the order.", example="123 Main St, New York, NY 10001")


class OrderCreate(OrderBase):
    """Model for creating a new order."""
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderUpdate(Base):
    """Model for updating an order's status or rider assignment."""
    status: Optional[str] = Field(None, description="New status of the order.", example="in_transit")
    rider_id: Optional[str] = Field(None, description="ID of the assigned delivery rider.", example="rider_xyz_456")


class OrderResponse(OrderBase):
    """Model for representing a full order in API responses."""
    id: str = Field(..., description="Unique order identifier.", example="ord_9z8y7x")
    user_id: str = Field(..., description="ID of the user who placed the order.", example="usr_5e6f7g")
    rider_id: Optional[str] = Field(None, description="ID of the assigned delivery rider.", example="rider_xyz_456")
    status: str = Field(..., description="Current status of the order.", example="in_transit")
    items: List[OrderItemResponse]
    subtotal: float = Field(..., description="Total price of items before fees.", example=21.50)
    delivery_fee: float = Field(..., description="Fee for delivery.", example=4.99)
    total_price: float = Field(..., description="Total price including all fees.", example=26.49)
    created_at: datetime = Field(..., description="Timestamp when the order was created.")
    delivered_at: Optional[datetime] = Field(None, description="Timestamp when the order was delivered.")