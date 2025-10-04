import math
import random
from datetime import datetime, timedelta
from typing import List, Dict

from fastapi import APIRouter, HTTPException, status, Query

# Assuming a models.py file in the same directory with Pydantic models
from .models import (
    Store,
    Product,
    InventoryItem,
    Order,
    OrderCreate,
    OrderItem,
    OrderStatus,
)

# --- APIRouter Setup ---
router = APIRouter(
    prefix="/api/v1",
    tags=["Grocery Delivery API"],
)

# --- In-Memory Database ---
# Using dictionaries for O(1) lookups by ID

STORES_DB: Dict[int, Store] = {
    1: Store(id=1, name="Downtown Central", lat=40.7128, lon=-74.0060, is_operational=True),
    2: Store(id=2, name="Brooklyn South", lat=40.6782, lon=-73.9442, is_operational=True),
    3: Store(id=3, name="Uptown Express", lat=40.7580, lon=-73.9855, is_operational=False),
    4: Store(id=4, name="Queens Local", lat=40.7282, lon=-73.7949, is_operational=True),
}

PRODUCTS_DB: Dict[int, Product] = {
    101: Product(id=101, name="Organic Bananas", price=1.50),
    102: Product(id=102, name="Whole Milk, 1 Gallon", price=4.25),
    103: Product(id=103, name="Artisan Sourdough Bread", price=5.99),
    104: Product(id=104, name="Free-Range Eggs, Dozen", price=6.50),
}

# Inventory format: {(store_id, product_id): quantity}
INVENTORY_DB: Dict[tuple[int, int], int] = {
    (1, 101): 50, (1, 102): 30, (1, 103): 20,
    (2, 101): 40, (2, 102): 25, (2, 103): 15, (2, 104): 40,
    (4, 101): 100, (4, 102): 80, (4, 104): 60,
}

ORDERS_DB: Dict[int, Order] = {}
_next_order_id = 1001


# --- Helper Functions ---
def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Euclidean distance between two GPS coordinates."""
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)


# --- API Endpoints ---

@router.get(
    "/stores/nearby",
    response_model=Store,
    summary="Find Closest Operational Store",
    description="Find the closest operational dark store based on the user's GPS coordinates.",
)
def find_nearby_store(
    lat: float = Query(..., description="User's latitude", ge=-90, le=90),
    lon: float = Query(..., description="User's longitude", ge=-180, le=180),
):
    """
    Finds the nearest operational store to the given latitude and longitude.

    A simple Euclidean distance is used for this in-memory simulation.
    In a real-world scenario, this would be a PostGIS spatial query.
    """
    operational_stores = [s for s in STORES_DB.values() if s.is_operational]

    if not operational_stores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No operational stores available at the moment.",
        )

    closest_store = min(
        operational_stores,
        key=lambda store: _calculate_distance(lat, lon, store.lat, store.lon),
    )

    return closest_store


@router.get(
    "/stores/{store_id}/inventory",
    response_model=List[InventoryItem],
    summary="Get Store Inventory",
    description="Retrieve all available products and their stock levels for a specific store.",
)
def get_store_inventory(store_id: int):
    """
    Retrieves the current inventory for a given store ID.
    """
    if store_id not in STORES_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found.",
        )

    inventory_items = []
    for (s_id, p_id), quantity in INVENTORY_DB.items():
        if s_id == store_id and quantity > 0:
            product = PRODUCTS_DB.get(p_id)
            if product:
                inventory_items.append(InventoryItem(product=product, quantity=quantity))

    return inventory_items


@router.post(
    "/orders",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Order",
    description="Create a new order. The backend validates stock levels in real-time before confirming the order.",
)
def create_order(order_payload: OrderCreate):
    """
    Creates a new order after validating store existence and product stock.
    This operation is 'atomic' for the in-memory simulation: it either
    fully succeeds or fails without changing inventory.
    """
    store_id = order_payload.store_id
    if store_id not in STORES_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found.",
        )
    if not STORES_DB[store_id].is_operational:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Store with ID {store_id} is currently not operational.",
        )

    order_items: List[OrderItem] = []
    # --- Validation Phase ---
    for item in order_payload.items:
        product = PRODUCTS_DB.get(item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item.product_id} not found.",
            )

        stock_key = (store_id, item.product_id)
        current_stock = INVENTORY_DB.get(stock_key, 0)

        if current_stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product '{product.name}'. Available: {current_stock}, Requested: {item.quantity}.",
            )
        order_items.append(OrderItem(product=product, quantity=item.quantity))

    # --- Execution Phase (if validation passes) ---
    for item in order_payload.items:
        stock_key = (store_id, item.product_id)
        INVENTORY_DB[stock_key] -= item.quantity

    global _next_order_id
    new_order_id = _next_order_id
    _next_order_id += 1

    created_time = datetime.utcnow()
    eta_minutes = random.randint(15, 45)
    
    new_order = Order(
        id=new_order_id,
        store_id=store_id,
        items=order_items,
        status=OrderStatus.CONFIRMED,
        created_at=created_time,
        estimated_delivery_time=created_time + timedelta(minutes=eta_minutes),
    )

    ORDERS_DB[new_order_id] = new_order
    return new_order


@router.get(
    "/orders/{order_id}",
    response_model=Order,
    summary="Get Order Status",
    description="Get the current status and details of a specific order, including items and ETA.",
)
def get_order(order_id: int):
    """
    Retrieves the details of a specific order by its ID.
    """
    order = ORDERS_DB.get(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found.",
        )
    return order