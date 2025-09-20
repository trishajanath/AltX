```python
from pydantic import BaseModel, Field, conint, confloat
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

#  Pydantic Models for Data Validation 
# SECURITY NOTE: Pydantic models are the first line of defense against malformed data and
# certain types of injection attacks. By enforcing strict data types and constraints (e.g., value ranges),
# we ensure that only valid data reaches our business logic.

#  Base Models 

class ReviewBase(BaseModel):
    user_name: str = Field(..., min_length=2, max_length=50, description="Name of the reviewer")
    rating: conint(ge=1, le=5) = Field(..., description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, max_length=500, description="Reviewer's comment")

class ReviewCreate(ReviewBase):
    pass

class Review(ReviewBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProductBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Product name")
    description: str = Field(..., min_length=10, description="Detailed product description")
    price: confloat(gt=0) = Field(..., description="Product price, must be positive")
    category: str = Field(..., min_length=3, max_length=50, description="Product category")
    stock_quantity: conint(ge=0) = Field(..., description="Available stock, cannot be negative")

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: UUID = Field(default_factory=uuid4)
    reviews: List[Review] = []

class OrderItemBase(BaseModel):
    product_id: UUID
    quantity: conint(gt=0) = Field(..., description="Quantity must be at least 1")

class OrderItem(OrderItemBase):
    pass

class OrderBase(BaseModel):
    # In a real app, this would be a user_id linked to an authenticated user
    customer_name: str = Field(..., min_length=2, max_length=100)
    shipping_address: str = Field(..., min_length=10, max_length=255)
    items: List[OrderItem]

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field("pending", description="Order status (e.g., pending, shipped, delivered)")
    total_price: float
```