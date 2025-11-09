import math
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

# Assume these models are defined in a file named `models.py` in the same directory.
# from .models import Product, PaginatedProductResponse, Cart, CartItem, User

# For self-containment, the models are defined here. In a real project,
# they would be in a separate `models.py` file as requested.
# --- Start of models.py content ---
from pydantic import BaseModel

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category: str
    tags: List[str]
    on_sale: bool

class PaginatedProductResponse(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    items: List[Product]

class CartItem(BaseModel):
    product: Product
    quantity: int

class Cart(BaseModel):
    user_id: int
    items: List[CartItem]
    total_price: float

class User(BaseModel):
    id: int
    username: str
    email: str
# --- End of models.py content ---


# --- In-Memory Storage ---

DB_PRODUCTS: List[Product] = [
    Product(id=1, name="Organic Bananas", description="A bunch of fresh, organic bananas.", price=1.99, category="produce", tags=["organic", "fruit"], on_sale=False),
    Product(id=2, name="Artisan Sourdough Bread", description="Handmade sourdough bread with a crispy crust.", price=5.49, category="bakery", tags=["artisan", "fresh"], on_sale=True),
    Product(id=3, name="Free-Range Eggs", description="One dozen large brown free-range eggs.", price=4.99, category="dairy", tags=["organic", "free-range"], on_sale=False),
    Product(id=4, name="Whole Milk", description="One gallon of whole milk.", price=3.50, category="dairy", tags=[], on_sale=False),
    Product(id=5, name="Gourmet Coffee Beans", description="Medium roast, single-origin coffee beans.", price=12.99, category="pantry", tags=["gourmet", "fair-trade"], on_sale=True),
    Product(id=6, name="Avocado", description="A single ripe avocado.", price=1.50, category="produce", tags=["organic", "fruit"], on_sale=True),
    Product(id=7, name="Cheddar Cheese Block", description="8oz sharp cheddar cheese block.", price=6.00, category="dairy", tags=["cheese"], on_sale=False),
    Product(id=8, name="Gluten-Free Pasta", description="16oz box of gluten-free penne pasta.", price=3.99, category="pantry", tags=["gluten-free"], on_sale=False),
    Product(id=9, name="Organic Spinach", description="A bag of fresh organic spinach.", price=3.29, category="produce", tags=["organic", "leafy-greens"], on_sale=True),
    Product(id=10, name="Dark Chocolate Bar", description="70% cacao dark chocolate bar.", price=2.99, category="pantry", tags=["organic", "gourmet"], on_sale=False),
]

# A dictionary to quickly look up products by ID
PRODUCT_LOOKUP: Dict[int, Product] = {p.id: p for p in DB_PRODUCTS}

# In-memory cart storage: {user_id: [{product_id: int, quantity: int}]}
DB_CARTS = {
    1: [
        {"product_id": 2, "quantity": 1},
        {"product_id": 5, "quantity": 2},
        {"product_id": 9, "quantity": 1},
    ]
}

# --- Dependency for simulating an authenticated user ---

async def get_current_user() -> User:
    """A dependency that simulates retrieving the current authenticated user."""
    # In a real app, this would involve decoding a JWT token or session cookie.
    return User(id=1, username="testuser", email="test@example.com")


# --- APIRouter Setup ---

router = APIRouter(
    prefix="/api/v1",
    tags=["E-commerce"],
)


# --- Route Implementations ---

@router.get("/products", response_model=PaginatedProductResponse)
async def get_products(
    category: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by."),
    on_sale: Optional[bool] = None,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
):
    """
    Retrieve a paginated list of products.
    Supports filtering by `category`, `tags`, and `on_sale` status.
    """
    filtered_products = list(DB_PRODUCTS)

    # Apply filters
    if category:
        filtered_products = [p for p in filtered_products if p.category.lower() == category.lower()]
    if on_sale is not None:
        filtered_products = [p for p in filtered_products if p.on_sale == on_sale]
    if tags:
        query_tags = {tag.strip().lower() for tag in tags.split(',')}
        filtered_products = [
            p for p in filtered_products if query_tags.issubset({t.lower() for t in p.tags})
        ]

    # Apply pagination
    total_items = len(filtered_products)
    total_pages = math.ceil(total_items / page_size)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_items = filtered_products[start_index:end_index]

    return PaginatedProductResponse(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        items=paginated_items,
    )


@router.get("/products/search", response_model=List[Product])
async def search_products(q: str = Query(..., min_length=3, description="Search query for product names and descriptions.")):
    """
    Performs a text-based search for products across names and descriptions.
    """
    search_term = q.lower()
    search_results = [
        p for p in DB_PRODUCTS
        if search_term in p.name.lower() or search_term in p.description.lower()
    ]
    return search_results


@router.get("/products/{product_id}", response_model=Product)
async def get_product_by_id(product_id: int):
    """
    Get detailed information for a single product by its ID.
    """
    product = PRODUCT_LOOKUP.get(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )
    return product


@router.get("/cart", response_model=Cart)
async def get_user_cart(current_user: User = Depends(get_current_user)):
    """
    Retrieve the contents of the current authenticated user's shopping cart.
    """
    user_cart_items = DB_CARTS.get(current_user.id, [])
    
    if not user_cart_items:
        return Cart(user_id=current_user.id, items=[], total_price=0.0)

    cart_items_response: List[CartItem] = []
    total_price = 0.0

    for item in user_cart_items:
        product = PRODUCT_LOOKUP.get(item["product_id"])
        if product:
            cart_items_response.append(
                CartItem(product=product, quantity=item["quantity"])
            )
            total_price += product.price * item["quantity"]
        # In a real application, you might want to handle cases where a
        # product_id in the cart no longer exists in the product database.

    return Cart(
        user_id=current_user.id,
        items=cart_items_response,
        total_price=round(total_price, 2),
    )