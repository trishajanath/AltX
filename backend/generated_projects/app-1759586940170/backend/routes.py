import uuid
from math import sqrt
from typing import List, Optional, Dict

from fastapi import APIRouter, HTTPException, status, Body, Query
from pydantic import BaseModel, Field

# --- Pydantic Models ---
# In a real application, these would be in a separate `models.py` file.
# from . import models

class Store(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    is_operational: bool

class Product(BaseModel):
    id: str
    name: str
    category: str
    price: float

class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    store_id: str
    items: List[OrderItem]
    payment_token: str

class Order(BaseModel):
    id: str
    status: str
    items: List[OrderItem]
    eta: str
    store_id: str


# --- In-Memory Storage ---
# This simulates a database for demonstration purposes.

db_stores: Dict[str, Store] = {
    "store-1": Store(id="store-1", name="Downtown Central", lat=34.0522, lon=-118.2437, is_operational=True),
    "store-2": Store(id="store-2", name="Hollywood Hub", lat=34.0928, lon=-118.3287, is_operational=True),
    "store-3": Store(id="store-3", name="Santa Monica Spot", lat=34.0195, lon=-118.4912, is_operational=False),
    "store-4": Store(id="store-4", name="Culver City Corner", lat=34.0211, lon=-118.3965, is_operational=True),
}

db_products: Dict[str, Product] = {
    "prod-1": Product(id="prod-1", name="Organic Milk", category="Dairy", price=3.50),
    "prod-2": Product(id="prod-2", name="Sourdough Bread", category="Bakery", price=4.75),
    "prod-3": Product(id="prod-3", name="Free-Range Eggs", category="Dairy", price=5.25),
    "prod-4": Product(id="prod-4", name="Avocado", category="Produce", price=1.99),
    "prod-5": Product(id="prod-5", name="Dark Chocolate Bar", category="Pantry", price=3.99),
}

# {store_id: {product_id: quantity}}
db_inventory: Dict[str, Dict[str, int]] = {
    "store-1": {
        "prod-1": 50,
        "prod-2": 30,
        "prod-3": 100,
        "prod-5": 40,
    },
    "store-2": {
        "prod-1": 40,
        "prod-2": 25,
        "prod-3": 80,
        "prod-4": 60,
        "prod-5": 20,
    },
    "store-4": {
        "prod-1": 10,
        "prod-2": 15,
        "prod-3": 0, # Out of stock
        "prod-4": 50,
        "prod-5": 30,
    }
}

db_orders: Dict[str, Order] = {}


# --- API Router ---

router = APIRouter(prefix="/api/v1")


# --- Helper Functions ---

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """A simple Euclidean distance calculation for demonstration."""
    return sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)


# --- Endpoints ---

@router.get(
    "/stores/nearby",
    response_model=Store,
    summary="Find the closest operational dark store",
    description="Find the closest operational dark store to a user's latitude and longitude to fetch the correct product inventory."
)
def get_nearby_store(lat: float = Query(..., example=34.06), lon: float = Query(..., example=-118.3)):
    """
    Finds the nearest operational store to the given latitude and longitude.
    """
    operational_stores = [s for s in db_stores.values() if s.is_operational]

    if not operational_stores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No operational stores available at the moment."
        )

    closest_store = min(
        operational_stores,
        key=lambda store: calculate_distance(lat, lon, store.lat, store.lon)
    )

    return closest_store


@router.get(
    "/products",
    response_model=List[Product],
    summary="List available products from a store",
    description="Retrieve a list of available products from a specific dark store, with support for category filtering and search."
)
def get_products(
    store_id: str = Query(..., example="store-1"),
    category: Optional[str] = Query(None, example="Dairy"),
    search_query: Optional[str] = Query(None, example="milk")
):
    """
    Retrieves a list of products for a given store, with optional filters.
    """
    store_inventory = db_inventory.get(store_id)
    if not store_inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID '{store_id}' not found."
        )

    # Get product IDs for products that are in stock (> 0)
    available_product_ids = {pid for pid, qty in store_inventory.items() if qty > 0}
    
    results = [db_products[pid] for pid in available_product_ids]

    if category:
        results = [p for p in results if p.category.lower() == category.lower()]

    if search_query:
        results = [p for p in results if search_query.lower() in p.name.lower()]

    return results


@router.post(
    "/orders",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="Create a new order from the user's cart. Validates stock levels before confirming the order."
)
def create_order(order_data: OrderCreate = Body(...)):
    """
    Creates a new order after validating store existence and product inventory.
    """
    # 1. Validate store
    if order_data.store_id not in db_stores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID '{order_data.store_id}' not found."
        )

    store_inventory = db_inventory.get(order_data.store_id, {})

    # 2. Validate products and check stock levels
    for item in order_data.items:
        if item.product_id not in db_products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{item.product_id}' not found."
            )
        
        current_stock = store_inventory.get(item.product_id, 0)
        if current_stock < item.quantity:
            product_name = db_products[item.product_id].name
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product_name}'. Available: {current_stock}, Requested: {item.quantity}."
            )

    # 3. "Process payment" (mock) and update inventory
    # In a real app, this would be a transactional operation.
    for item in order_data.items:
        store_inventory[item.product_id] -= item.quantity

    # 4. Create and save the order
    new_order_id = str(uuid.uuid4())
    new_order = Order(
        id=new_order_id,
        status="picking",
        items=order_data.items,
        eta="12 minutes", # Mock ETA
        store_id=order_data.store_id
    )
    db_orders[new_order_id] = new_order

    return new_order


@router.get(
    "/orders/{order_id}",
    response_model=Order,
    summary="Get order status and details",
    description="Get the current status and details of a specific order."
)
def get_order(order_id: str):
    """
    Retrieves the details and status of a specific order by its ID.
    """
    order = db_orders.get(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' not found."
        )
    return order