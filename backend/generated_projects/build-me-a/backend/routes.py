```python
import uuid
import random
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Path, status, Body

from . import models

# Create an APIRouter instance. This helps in organizing endpoints.
router = APIRouter()

# =============================================================================
# In-Memory "Database"
# In a real application, this data would come from a database like PostgreSQL.
# For this example, we mock the data to ensure endpoints are fully functional.
# =============================================================================

CATEGORIES = {
    "electronics": "Electronics",
    "clothing": "Clothing & Apparel",
    "home_goods": "Home & Garden",
    "sports": "Sports & Outdoors",
    "books": "Books & Literature"
}

# Generate more diverse mock products
MOCK_PRODUCTS: List[models.ProductInDB] = []
for i in range(120):
    cat_id, cat_name = random.choice(list(CATEGORIES.items()))
    base_price = round(random.uniform(5.0, 500.0), 2)
    product = models.ProductInDB(
        id=uuid.uuid4(),
        name=f"{cat_name} Product {i+1}",
        description=f"High-quality and durable product from the {cat_name} category. Item number {i+1}. Perfect for your needs.",
        price=base_price * random.uniform(0.7, 0.95),  # Discounted price
        original_price=base_price if random.random() > 0.3 else None,
        category=cat_name,
        image_url=f"https://picsum.photos/seed/{i+1}/400/300",
        rating=round(random.uniform(3.0, 5.0), 1),
        review_count=random.randint(5, 5000),
        tags=[cat_id, "popular", "on-sale"] if i % 5 == 0 else [cat_id]
    )
    MOCK_PRODUCTS.append(product)

MOCK_REVIEWS: List[models.Review] = [
    models.Review(
        id=uuid.uuid4(),
        product_id=MOCK_PRODUCTS[0].id,
        username="Alice",
        rating=5,
        comment="Absolutely fantastic! Best purchase of the year."
    ),
    models.Review(
        id=uuid.uuid4(),
        product_id=MOCK_PRODUCTS[0].id,
        username="Bob",
        rating=4,
        comment="Very good, but the battery could last a bit longer."
    )
]

# =============================================================================
# API Endpoints
# =============================================================================

@router.get(
    "/products",
    response_model=models.PaginatedProductsResponse,
    summary="List Products with Filtering and Pagination",
    tags=["Products"]
)
def list_products(
    search: Optional[str] = Query(None, description="Search query to filter by product name or description."),
    category: Optional[str] = Query(None, description="Filter by category name (e.g., 'Electronics')."),
    min_price: Optional[float] = Query(None, gt=0, description="Minimum price filter."),
    max_price: Optional[float] = Query(None, gt=0, description="Maximum price filter."),
    page: int = Query(1, ge=1, description="Page number for pagination."),
    size: int = Query(20, ge=1, le=100, description="Number of items per page.")
):
    """
    Retrieves a paginated list of products. Supports filtering by search query,
    category, and price range.
    """
    filtered_products = MOCK_PRODUCTS

    # Apply filters
    if search:
        search_lower = search.lower()
        filtered_products = [
            p for p in filtered_products 
            if search_lower in p.name.lower() or search_lower in p.description.lower()
        ]
    if category:
        filtered_products = [p for p in filtered_products if p.category.lower() == category.lower()]
    if min_price:
        filtered_products = [p for p in filtered_products if p.price >= min_price]
    if max_price:
        filtered_products = [p for p in filtered_products if p.price <= max_price]

    # Apply pagination
    total_items = len(filtered_products)
    start_index = (page - 1) * size
    end_index = start_index + size
    paginated_items = filtered_products[start_index:end_index]

    return models.PaginatedProductsResponse(
        total=total_items,
        page=page,
        size=len(paginated_items), # Return the actual number of items on the page
        items=paginated_items
    )

@router.get(
    "/products/{product_id}",
    response_model=models.Product,
    summary="Get a Single Product by ID",
    tags=["Products"],
    responses={404: {"description": "Product not found"}}
)
def get_product(product_id: uuid.UUID = Path(..., description="The UUID of the product to retrieve.")):
    """
    Retrieves detailed information for a specific product by its unique ID.
    """
    product = next((p for p in MOCK_PRODUCTS if p.id == product_id), None)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.get(
    "/categories",
    response_model=List[models.Category],
    summary="List All Product Categories",
    tags=["Categories"]
)
def list_categories():
    """
    Retrieves a list of all available product categories along with the count
    of products in each category.
    """
    category_counts = {cat_name: 0 for cat_name in CATEGORIES.values()}
    for product in MOCK_PRODUCTS:
        if product.category in category_counts:
            category_counts[product.category] += 1
    
    # Map back to category IDs (slugs)
    id_map = {v: k for k, v in CATEGORIES.items()}

    return [
        models.Category(id=id_map[name], name=name, product_count=count)
        for name, count in category_counts.items()
    ]

@router.get(
    "/products/{product_id}/reviews",
    response_model=List[models.Review],
    summary="Get Reviews for a Product",
    tags=["Reviews"]
)
def get_product_reviews(product_id: uuid.UUID = Path(..., description="The UUID of the product.")):
    """
    Retrieves all reviews associated with a specific product ID.
    """
    # First, check if the product exists to provide a clear 404
    if not any(p.id == product_id for p in MOCK_PRODUCTS):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    return [r for r in MOCK_REVIEWS if r.product_id == product_id]

@router.post(
    "/products/{product_id}/reviews",
    response_model=models.Review,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a New Review",
    tags=["Reviews"],
    responses={404: {"description": "Product not found"}}
)
def create_product_review(
    product_id: uuid.UUID = Path(..., description="The UUID of the product to review."),
    review_data: models.ReviewCreate = Body(...)
):
    """
    Adds a new review to a specific product. The new review is added to the
    in-memory list and returned in the response.
    """
    # Check if product exists
    product = next((p for p in MOCK_PRODUCTS if p.id == product_id), None)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    new_review = models.Review(
        product_id=product_id,
        **review_data.model_dump()
    )
    MOCK_REVIEWS.append(new_review)

    # Optional: Update product's rating and review count (simulates real-world logic)
    product.review_count += 1
    # Simple average calculation
    current_total_rating = (product.rating * (product.review_count - 1))
    new_avg_rating = (current_total_rating + new_review.rating) / product.review_count
    product.rating = round(new_avg_rating, 1)

    return new_review
```