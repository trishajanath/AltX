```python
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum

#  Enums for controlled vocabularies 

class OrderStatus(str, Enum):
    """
    Enum for the possible statuses of an order. Using an Enum ensures data consistency.
    """
    PLACED = "placed"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

#  Core Data Models 
# These models represent the main entities in our application.

class Product(BaseModel):
    """
    Represents a product available for delivery.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="Price must be positive")
    image_url: Optional[str] = None
    stock_quantity: int = Field(..., ge=0, description="Stock cannot be negative")

class Store(BaseModel):
    """
    Represents a store or dark store from where deliveries originate.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    address: str
    latitude: float
    longitude: float
    inventory: List[Product] = []

#  Request/Response Models for API Endpoints 
# These models define the shape of data for API requests and responses.

class OrderItemCreate(BaseModel):
    """
    Model for an item within a new order request. Validates the product ID and quantity.
    """
    product_id: uuid.UUID
    quantity: int = Field(..., gt=0, description="Quantity must be at least 1")

class OrderCreateRequest(BaseModel):
    """
    Request model for creating a new order.
    """
    store_id: uuid.UUID
    # A dummy user_id since we have no authentication
    user_id: str = "guest_user"
    items: List[OrderItemCreate] = Field(..., min_items=1)

class OrderItemResponse(BaseModel):
    """
    Response model for an item within a created order, including pricing details.
    """
    product_id: uuid.UUID
    product_name: str
    quantity: int
    price_per_item: float

class OrderResponse(BaseModel):
    """
    The complete response model for an order, providing all necessary details.
    This is the data structure the frontend will receive.
    """
    id: uuid.UUID
    store_id: uuid.UUID
    user_id: str
    items: List[OrderItemResponse]
    total_amount: float
    status: OrderStatus
    created_at: datetime
    estimated_delivery_time: datetime

    class Config:
        # Allows Pydantic to work with non-dict objects (ORM mode)
        # and correctly serialize Enum members to their string values.
        from_attributes = True

class OrderStatusUpdateRequest(BaseModel):
    """
    Request model for updating an order's status.
    """
    status: OrderStatus
```