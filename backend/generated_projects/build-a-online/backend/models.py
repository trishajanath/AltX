```python
from pydantic import BaseModel, Field, EmailStr, conlist
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

#  Enums for strict data validation 

class ClothingCategory(str, Enum):
    """Enumeration for clothing categories."""
    TSHIRT = "T-Shirt"
    JEANS = "Jeans"
    DRESS = "Dress"
    JACKET = "Jacket"
    SWEATER = "Sweater"
    ACCESSORIES = "Accessories"

class ClothingSize(str, Enum):
    """Enumeration for clothing sizes."""
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"

#  Seller/User Models 

class SellerBase(BaseModel):
    """Base model for a seller."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username for the seller.")
    email: EmailStr = Field(..., description="Seller's email address.")
    store_name: str = Field(..., min_length=3, max_length=100, description="The name of the seller's store.")

class SellerCreate(SellerBase):
    """Model for creating a new seller. No extra fields needed for now."""
    pass

class Seller(SellerBase):
    """Response model for a seller, including their unique ID."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True # Kept for compatibility if you switch to an ORM
        from_attributes = True

#  Product Models 

class ProductBase(BaseModel):
    """Base model for a clothing product."""
    name: str = Field(..., min_length=3, max_length=100, description="Name of the product.")
    description: str = Field(..., max_length=500, description="Detailed description of the product.")
    price: float = Field(..., gt=0, description="Price of the product in USD. Must be greater than zero.")
    category: ClothingCategory = Field(..., description="Category of the clothing item.")
    available_sizes: List[ClothingSize] = Field(..., description="List of available sizes for the product.")
    seller_id: UUID = Field(..., description="The ID of the seller listing this product.")

class ProductCreate(ProductBase):
    """Model for creating a new product."""
    pass

class ProductUpdate(BaseModel):
    """Model for updating an existing product. All fields are optional."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[ClothingCategory] = None
    available_sizes: Optional[List[ClothingSize]] = None

class Product(ProductBase):
    """Response model for a product, including generated fields."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True
        from_attributes = True

#  Order Models 

class OrderItem(BaseModel):
    """Model representing an item within an order."""
    product_id: UUID
    quantity: int = Field(..., gt=0, description="Quantity of the product. Must be at least 1.")

class OrderCreate(BaseModel):
    """Model for creating a new order."""
    customer_email: EmailStr = Field(..., description="Email of the customer placing the order.")
    items: conlist(OrderItem, min_length=1) = Field(..., description="List of items in the order. Must not be empty.")

class Order(BaseModel):
    """Response model for an order."""
    id: UUID = Field(default_factory=uuid4)
    customer_email: EmailStr
    items: List[OrderItem]
    total_price: float = Field(..., description="Calculated total price of the order.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field("Pending", description="Current status of the order.")
    
    class Config:
        orm_mode = True
        from_attributes = True
```