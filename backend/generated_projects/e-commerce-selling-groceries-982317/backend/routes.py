# In a real application, these models would be in a separate file, e.g., `models.py`.
# For this exercise, we'll define them here and then import them to satisfy the requirement.
#
# --- hypothetical models.py ---
# from pydantic import BaseModel, Field
# from typing import List, Dict, Any, Optional
#
# class Review(BaseModel):
#     username: str
#     rating: int = Field(..., ge=1, le=5)
#     comment: str
#
# class Product(BaseModel):
#     id: int
#     name: str
#     description: str
#     price: float
#     category: str
#     attributes: Dict[str, Any]
#     reviews: List[Review] = []
#
# class ComparisonRequest(BaseModel):
#     product_ids: List[int] = Field(..., min_items=2)
#
# class CartItem(BaseModel):
#     product_id: int
#     quantity: int
#
# class Cart(BaseModel):
#     items: List[CartItem]
#     total_price: float
# --- end of models.py ---


from fastapi import APIRouter, HTTPException, Request, status, Body
from typing import List, Optional, Dict, Any

# Assuming the models are in a file named `models.py` in the same directory
from .models import Product, ComparisonRequest, Cart, CartItem, Review

# --- In-Memory Database ---

DB_REVIEWS = {
    1: [
        Review(username="Alice", rating=5, comment="Amazing phone, great camera!"),
        Review(username="Bob", rating=4, comment="Fast and reliable, but battery could be better."),
    ],
    2: [
        Review(username="Charlie", rating=5, comment="Sleek design and powerful performance."),
    ],
    3: [
        Review(username="Alice", rating=3, comment="Good laptop, but it gets a bit hot under load."),
    ],
}

DB_PRODUCTS: List[Product] = [
    Product(
        id=1,
        name="QuantumPhone X",
        description="The latest smartphone with a quantum-entangled camera.",
        price=1199.99,
        category="Electronics",
        attributes={"brand": "QuantumLeap", "storage": "256GB", "color": "Nebula Black", "screen_size": "6.7 inches"},
        reviews=DB_REVIEWS.get(1, [])
    ),
    Product(
        id=2,
        name="Galaxy Weaver S25",
        description="A smartphone that weaves reality with its holographic display.",
        price=1099.50,
        category="Electronics",
        attributes={"brand": "Samsung", "storage": "512GB", "color": "Cosmic Silver", "screen_size": "6.8 inches"},
        reviews=DB_REVIEWS.get(2, [])
    ),
    Product(
        id=3,
        name="NovaBook Pro",
        description="A powerful laptop for creative professionals.",
        price=2499.00,
        category="Computers",
        attributes={"brand": "Apple", "storage": "1TB SSD", "color": "Space Gray", "processor": "M4 Pro"},
        reviews=DB_REVIEWS.get(3, [])
    ),
    Product(
        id=4,
        name="ChronoWatch Series 9",
        description="A smartwatch that can predict the weather with 99% accuracy.",
        price=499.00,
        category="Wearables",
        attributes={"brand": "QuantumLeap", "color": "Midnight Blue", "water_resistant": "50m"},
        reviews=[]
    ),
    Product(
        id=5,
        name="Pixel Weaver 9",
        description="Google's flagship with AI-powered everything.",
        price=999.00,
        category="Electronics",
        attributes={"brand": "Google", "storage": "256GB", "color": "Obsidian"},
        reviews=[]
    ),
]

DB_CART: List[CartItem] = [
    CartItem(product_id=1, quantity=1),
    CartItem(product_id=3, quantity=1),
]

# --- API Router ---

router = APIRouter(
    prefix="/api/v1",
    tags=["E-commerce"],
)

# Helper function to find a product by ID
def find_product_by_id(product_id: int) -> Optional[Product]:
    """Finds a product in the in-memory DB by its ID."""
    for product in DB_PRODUCTS:
        if product.id == product_id:
            return product
    return None

# --- Endpoints ---

@router.get("/products", response_model=List[Product])
async def list_products(
    request: Request,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """
    List all products with filtering by category, search query, and dynamic attributes.
    Dynamic attributes are passed as query parameters with a prefix, e.g., `attributes.brand=Apple`.
    """
    results = list(DB_PRODUCTS)

    # Filter by category
    if category:
        results = [p for p in results if p.category.lower() == category.lower()]

    # Filter by search query (in name and description)
    if search:
        search_lower = search.lower()
        results = [
            p for p in results
            if search_lower in p.name.lower() or search_lower in p.description.lower()
        ]

    # Filter by dynamic attributes
    attribute_filters = {}
    for key, value in request.query_params.items():
        if key.startswith("attributes."):
            attr_name = key.split(".", 1)[1]
            attribute_filters[attr_name] = value

    if attribute_filters:
        results = [
            p for p in results
            if all(
                str(p.attributes.get(key)).lower() == str(value).lower()
                for key, value in attribute_filters.items()
            )
        ]

    return results


@router.get("/products/{product_id}", response_model=Product)
async def get_product_details(product_id: int):
    """
    Retrieve detailed information for a single product, including its
    specifications and user reviews.
    """
    product = find_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    return product


@router.post("/products/compare", response_model=Dict[str, List[Any]])
async def compare_products(request: ComparisonRequest):
    """
    Accept a list of product IDs and return a structured JSON object
    for side-by-side comparison.
    """
    products_to_compare: List[Product] = []
    for pid in request.product_ids:
        product = find_product_by_id(pid)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {pid} not found for comparison"
            )
        products_to_compare.append(product)

    # Build a structured comparison dictionary
    comparison_data: Dict[str, List[Any]] = {
        "id": [],
        "name": [],
        "price": [],
        "category": [],
    }
    
    # Gather all unique attribute keys from all products being compared
    all_attribute_keys = set()
    for p in products_to_compare:
        all_attribute_keys.update(p.attributes.keys())

    # Initialize lists for each attribute
    for key in sorted(list(all_attribute_keys)):
        comparison_data[key] = []

    # Populate the comparison data
    for p in products_to_compare:
        comparison_data["id"].append(p.id)
        comparison_data["name"].append(p.name)
        comparison_data["price"].append(p.price)
        comparison_data["category"].append(p.category)
        for key in sorted(list(all_attribute_keys)):
            comparison_data[key].append(p.attributes.get(key, "N/A"))

    return comparison_data


@router.get("/cart", response_model=Cart)
async def get_cart_contents():
    """
    Retrieve the contents of the current user's shopping cart.
    For this example, it's a single, shared in-memory cart.
    """
    total_price = 0.0
    detailed_items = []

    for item in DB_CART:
        product = find_product_by_id(item.product_id)
        if product:
            total_price += product.price * item.quantity
            detailed_items.append(item)
        # In a real app, you might handle cases where a product in cart is no longer available

    return Cart(items=detailed_items, total_price=round(total_price, 2))