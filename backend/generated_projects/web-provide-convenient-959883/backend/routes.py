import re
from typing import List, Optional, Dict

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

# --- Pydantic Models (as if imported from a .models file) ---
# from .models import Product, CartItem, CartItemAdd

class Product(BaseModel):
    """Represents a product in the store."""
    id: int
    name: str
    description: str
    price: float
    category: str
    brand: str
    tags: List[str]

class CartItemAdd(BaseModel):
    """Schema for adding a new item to the cart."""
    product_id: int
    quantity: int = Field(1, gt=0, description="Quantity must be greater than 0")

class CartItem(BaseModel):
    """Represents an item within the shopping cart, including full product details."""
    product: Product
    quantity: int

# --- In-Memory Database Simulation ---

db_products: List[Product] = [
    Product(id=1, name="Organic Milk", description="Fresh, whole organic milk.", price=3.99, category="Dairy", brand="FarmFresh", tags=["organic", "milk", "dairy"]),
    Product(id=2, name="Sourdough Bread", description="Artisanal sourdough loaf.", price=5.49, category="Bakery", brand="Baker's Delight", tags=["bread", "sourdough", "organic"]),
    Product(id=3, name="Cheddar Cheese", description="Aged sharp cheddar cheese.", price=7.99, category="Dairy", brand="CheeseMasters", tags=["cheese", "dairy"]),
    Product(id=4, name="Free-Range Eggs", description="One dozen large free-range eggs.", price=4.99, category="Dairy", brand="FarmFresh", tags=["eggs", "organic", "free-range"]),
    Product(id=5, name="Gala Apples", description="A bag of crisp Gala apples.", price=6.20, category="Produce", brand="OrchardBest", tags=["fruit", "apples"]),
    Product(id=6, name="Organic Chicken Breast", description="Skinless, boneless organic chicken breast.", price=12.50, category="Meat", brand="FarmFresh", tags=["chicken", "meat", "organic"]),
    Product(id=7, name="Whole Wheat Bread", description="Healthy whole wheat bread.", price=4.50, category="Bakery", brand="Baker's Delight", tags=["bread", "whole-wheat"]),
]

# The cart stores product_id -> quantity
db_cart: Dict[int, int] = {}

# --- Helper function to find a product by ID ---

def find_product_by_id(product_id: int) -> Optional[Product]:
    """Finds a product in the mock database by its ID."""
    for product in db_products:
        if product.id == product_id:
            return product
    return None

# --- API Router Setup ---

router = APIRouter(
    prefix="/api/v1",
    tags=["E-commerce"],
)

# --- Route Implementations ---

@router.get(
    "/products",
    response_model=List[Product],
    summary="Get a list of products",
    description="Retrieve a paginated list of products. Supports query parameters for filtering by `category`, `brand`, and `tags` (e.g., /api/v1/products?category=Dairy&tags=organic)."
)
def get_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by"),
    skip: int = 0,
    limit: int = 10
):
    """
    Retrieves a list of products with optional filtering and pagination.
    """
    filtered_products = db_products

    if category:
        filtered_products = [p for p in filtered_products if p.category.lower() == category.lower()]

    if brand:
        filtered_products = [p for p in filtered_products if p.brand.lower() == brand.lower()]

    if tags:
        required_tags = {tag.strip().lower() for tag in tags.split(',')}
        filtered_products = [
            p for p in filtered_products if required_tags.issubset(set(t.lower() for t in p.tags))
        ]

    return filtered_products[skip : skip + limit]


@router.get(
    "/products/search",
    response_model=List[Product],
    summary="Search for products",
    description="Performs a full-text search on products based on a query string `q`. Returns a list of matching products ranked by relevance."
)
def search_products(q: str = Query(..., min_length=3, description="The search query string.")):
    """
    Performs a case-insensitive search on product names and descriptions.
    Results are ranked with matches in the name being more relevant.
    """
    query_lower = q.lower()
    
    # Simple relevance scoring: 2 for name match, 1 for description match
    scored_results = []
    for product in db_products:
        score = 0
        if re.search(r'\b' + re.escape(query_lower) + r'\b', product.name.lower()):
            score += 2
        if re.search(r'\b' + re.escape(query_lower) + r'\b', product.description.lower()):
            score += 1
        
        if score > 0:
            scored_results.append({"product": product, "score": score})

    # Sort by score descending
    sorted_results = sorted(scored_results, key=lambda x: x["score"], reverse=True)
    
    return [result["product"] for result in sorted_results]


@router.get(
    "/cart",
    response_model=List[CartItem],
    summary="Get the shopping cart",
    description="Fetches the contents of the authenticated user's current shopping cart."
)
def get_cart():
    """
    Retrieves the current shopping cart, populating product details for each item.
    """
    cart_items = []
    for product_id, quantity in db_cart.items():
        product = find_product_by_id(product_id)
        if product: # Should always be true if cart is managed correctly
            cart_items.append(CartItem(product=product, quantity=quantity))
    return cart_items


@router.post(
    "/cart/items",
    response_model=CartItem,
    status_code=201,
    summary="Add an item to the cart",
    description='Adds a new product to the cart or increments its quantity. Body: `{"product_id": 123, "quantity": 1}`.'
)
def add_item_to_cart(item: CartItemAdd = Body(...)):
    """
    Adds a product to the cart. If the product is already in the cart,
    its quantity is incremented by the specified amount.
    """
    product = find_product_by_id(item.product_id)
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {item.product_id} not found."
        )

    # Add to or update the cart
    current_quantity = db_cart.get(item.product_id, 0)
    db_cart[item.product_id] = current_quantity + item.quantity
    
    return CartItem(product=product, quantity=db_cart[item.product_id])