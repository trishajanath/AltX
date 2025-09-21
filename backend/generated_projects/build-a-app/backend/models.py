```python
import uuid
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

#  Base Models & Enums 

class OrderStatus(str, Enum):
    """Enumeration for possible order statuses."""
    PLACED = "placed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

#  Menu Item Models 

class MenuItem(BaseModel):
    """Represents a single item on a restaurant's menu."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str = Field(..., min_length=1, max_length=100, description="Name of the menu item")
    description: str = Field(..., max_length=500, description="Detailed description of the item")
    price: float = Field(..., gt=0, description="Price of the item, must be positive")
    image_url: Optional[str] = Field(None, description="URL for an image of the item")

#  Restaurant Models 

class RestaurantBase(BaseModel):
    """Base model for a restaurant, containing common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    cuisine_type: str = Field(..., min_length=1, max_length=50)
    address: str = Field(..., min_length=10, max_length=255)
    rating: float = Field(..., ge=1.0, le=5.0, description="Customer rating from 1.0 to 5.0")

class Restaurant(RestaurantBase):
    """Full restaurant model, including its unique ID and full menu."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    menu: List[MenuItem] = []

class RestaurantListResponse(RestaurantBase):
    """A simplified restaurant model for listing purposes, excluding the full menu."""
    id: uuid.UUID

#  Order Models 

class OrderItemCreate(BaseModel):
    """Model for creating a new item within an order request."""
    menu_item_id: uuid.UUID
    quantity: int = Field(..., gt=0, description="Quantity must be a positive integer")

class OrderCreateRequest(BaseModel):
    """Request model for creating a new order."""
    restaurant_id: uuid.UUID
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Must contain at least one item")

class OrderItemResponse(BaseModel):
    """Response model for an item within a placed order."""
    menu_item_name: str
    quantity: int
    price_per_item: float

class OrderResponse(BaseModel):
    """Full response model for a created or retrieved order."""
    id: uuid.UUID
    restaurant_id: uuid.UUID
    items: List[OrderItemResponse]
    total_amount: float
    status: OrderStatus
    created_at: datetime
    
```