```python
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, conint, conlist
from typing import List, Optional

# =============================================================================
# Base Models & Common Schemas
# =============================================================================

class ProductBase(BaseModel):
    """Base model for product data, containing common fields."""
    name: str = Field(..., min_length=1, max_length=100, examples=["Wireless Noise-Cancelling Headphones"])
    description: str = Field(..., min_length=10, examples=["Experience immersive sound with our latest headphones featuring active noise cancellation and 30-hour battery life."])
    price: float = Field(..., gt=0, examples=[99.99])
    category: str = Field(..., examples=["Electronics"])
    image_url: HttpUrl = Field(..., examples=["https://example.com/images/headphones.jpg"])

class Product(ProductBase):
    """Full product model including dynamic and generated fields."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, examples=[uuid.uuid4()])
    original_price: Optional[float] = Field(None, gt=0, description="The price before discount, if any.", examples=[129.99])
    rating: float = Field(..., ge=0, le=5, examples=[4.5])
    review_count: int = Field(..., ge=0, examples=[1500])
    tags: List[str] = Field(default_factory=list, examples=[["audio", "bluetooth", "travel"]])
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class ProductInDB(Product):
    """Represents a product as stored in our 'database' (in-memory list)."""
    pass

class PaginatedProductsResponse(BaseModel):
    """Response model for paginated product listings."""
    total: int = Field(..., description="Total number of products matching the query.", examples=[120])
    page: int = Field(..., gt=0, description="Current page number.", examples=[1])
    size: int = Field(..., gt=0, description="Number of items per page.", examples=[20])
    items: List[Product] = Field(..., description="List of products for the current page.")

class Category(BaseModel):
    """Model for a product category."""
    id: str = Field(..., examples=["electronics"])
    name: str = Field(..., examples=["Electronics"])
    product_count: int = Field(..., ge=0, examples=[50])

# =============================================================================
# Review Models
# =============================================================================

class ReviewBase(BaseModel):
    """Base model for creating a new review."""
    username: str = Field(..., min_length=2, max_length=50, examples=["JohnDoe"])
    rating: conint(ge=1, le=5) = Field(..., description="Rating from 1 to 5.", examples=[5])
    comment: Optional[str] = Field(None, max_length=1000, examples=["Amazing product, highly recommend!"])

class ReviewCreate(ReviewBase):
    """The model used for the POST request body when creating a review."""
    pass

class Review(ReviewBase):
    """Full review model including server-generated fields."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    product_id: uuid.UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
```