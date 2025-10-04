import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
import random

from fastapi import APIRouter, HTTPException, status, Body, Query
from pydantic import BaseModel, Field

# --- Pydantic Models (should be in a separate models.py file) ---

class GeoPoint(BaseModel):
    """Represents a geographical point."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")

class StoreCoverage(BaseModel):
    """Represents the coverage area of a store using a simple bounding box."""
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float

class Store(BaseModel):
    """Represents a dark store."""
    id: int
    name: str
    is_operational: bool
    coverage: StoreCoverage

class Product(BaseModel):
    """Represents a product available for sale."""
    id: int
    name: str
    category: str
    price: float

class ProductWithInventory(Product):
    """Extends Product model to include real-time inventory level."""
    inventory_level: int

class OrderItemCreate(BaseModel):
    """Represents an item within a new order request."""
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    """Request model for creating a new order."""
    store_id: int
    items: List[OrderItemCreate]

class OrderStatusEnum(str, Enum):
    """Enum for possible order statuses."""
    PENDING = "pending"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderStatusResponse(BaseModel):
    """Response model for the order status endpoint."""
    order_id: uuid.UUID
    status: OrderStatusEnum
    rider_location: Optional[GeoPoint] = None
    estimated_delivery_time: datetime

class Order(BaseModel):
    """Represents a created order in the system."""
    id: uuid.UUID
    store_id: int
    items: List[OrderItemCreate]
    status: OrderStatusEnum
    rider_id: Optional[int] = None
    estimated_delivery_time: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- In-Memory Storage (simulating a database) ---

DB_STORES: Dict[int, Store] = {
    1: Store(
        id=1,
        name="Dark Store - Downtown Manhattan",
        is_operational=True,
        coverage=StoreCoverage(min_lat=40.70, max_lat=40.74, min_lng=-74.02, max_lng=-73.98)
    ),
    2: Store(
        id=2,
        name="Dark Store - Midtown",
        is_operational=True,
        coverage=StoreCoverage(min_lat=40.74, max_lat=40.78, min_lng=-74.00, max_lng=-73.96)
    ),
    3: Store(
        id=3,
        name="Dark Store - Brooklyn (Offline)",
        is_operational=False,
        coverage=StoreCoverage(min_lat=40.67, max_lat=40.71, min_lng=-74.00, max_lng=-73.94)
    ),
}

DB_PRODUCTS: Dict[int, Product] = {
    101: Product(id=101, name="Organic Bananas", category="fruits", price=1.50),
    102: Product(id=102, name="Whole Milk, 1L", category="dairy", price=3.25),
    201: Product(id=201, name="Kettle Chips - Sea Salt", category="snacks", price=4.99),
    202: Product(id=202, name="Chocolate Bar", category="snacks", price=2.79),
    301: Product(id=301, name="Sparkling Water", category="beverages", price=1.99),
}

# Inventory is a dict with (store_id, product_id) as key and quantity as value
DB_INVENTORY: Dict[tuple[int, int], int] = {
    (1, 101): 50, (1, 102): 30, (1, 201): 100, (1, 202): 5, (1, 301): 80,
    (2, 101): 40, (2, 102): 0, (2, 201): 120, (2, 202): 75, (2, 301): 60,
}

DB_RIDERS: Dict[int, Dict[str, Any]] = {
    1: {"name": "John D.", "location": GeoPoint(lat=40.71, lng=-74.00)},
    2: {"name": "Jane S.", "location": GeoPoint(lat=40.75, lng=-73.98)},
}

DB_ORDERS: Dict[uuid.UUID, Order] = {}


# --- API Router Setup ---

router = APIRouter(
    prefix="/api/v1",
    tags=["E-commerce Quick Delivery"],
)


# --- Helper Functions ---

def find_store_by_id(store_id: int) -> Optional[Store]:
    return DB_STORES.get(store_id)

def find_order_by_id(order_id: uuid.UUID) -> Optional[Order]:
    return DB_ORDERS.get(order_id)

def get_inventory_level(store_id: int, product_id: int) -> int:
    return DB_INVENTORY.get((store_id, product_id), 0)


# --- API Endpoints ---

@router.get(
    "/stores/nearby",
    response_model=Store,
    summary="Find nearest operational store"
)
def get_nearby_store(
    lat: float = Query(..., description="User's latitude", example=40.7128),
    lng: float = Query(..., description="User's longitude", example=-74.0060)
):
    """
    Find the operational dark store for the user's coordinates and return its
    ID and coverage area.
    """
    for store in DB_STORES.values():
        if store.is_operational:
            cov = store.coverage
            if cov.min_lat <= lat <= cov.max_lat and cov.min_lng <= lng <= cov.max_lng:
                return store
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No operational store found for your location."
    )

@router.get(
    "/stores/{store_id}/products",
    response_model=List[ProductWithInventory],
    summary="Get available products for a store"
)
def get_store_products(
    store_id: int,
    category: Optional[str] = Query(None, description="Filter by product category", example="snacks"),
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: int = Query(10, ge=1, le=100, description="Pagination limit")
):
    """
    Retrieve all available products for a specific store, with real-time
    inventory levels and pagination.
    """
    if not find_store_by_id(store_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found."
        )

    # Get all product IDs that have inventory in the specified store
    store_product_ids = {
        prod_id for store, prod_id in DB_INVENTORY.keys() if store == store_id
    }

    # Filter products based on store and category
    filtered_products = []
    for product_id in store_product_ids:
        product = DB_PRODUCTS.get(product_id)
        if product:
            if category and product.category.lower() != category.lower():
                continue
            filtered_products.append(product)

    # Add inventory levels and apply pagination
    results = []
    for product in filtered_products[skip : skip + limit]:
        inventory_level = get_inventory_level(store_id, product.id)
        if inventory_level > 0:
            results.append(
                ProductWithInventory(**product.model_dump(), inventory_level=inventory_level)
            )

    return results

@router.post(
    "/orders",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order"
)
def create_order(order_data: OrderCreate = Body(...)):
    """
    Create a new order. The backend validates stock, calculates ETA,
    and assigns the order to the nearest available rider.
    """
    store = find_store_by_id(order_data.store_id)
    if not store or not store.is_operational:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Store with ID {order_data.store_id} is not available."
        )

    if not order_data.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item."
        )

    # Stock validation
    for item in order_data.items:
        if item.product_id not in DB_PRODUCTS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item.product_id} not found."
            )
        inventory_level = get_inventory_level(order_data.store_id, item.product_id)
        if inventory_level < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for product ID {item.product_id}. Available: {inventory_level}, Requested: {item.quantity}"
            )

    # If all checks pass, deduct stock
    for item in order_data.items:
        inventory_key = (order_data.store_id, item.product_id)
        DB_INVENTORY[inventory_key] -= item.quantity

    # Simulate ETA calculation and rider assignment
    eta = datetime.utcnow() + timedelta(minutes=random.randint(15, 45))
    assigned_rider_id = random.choice(list(DB_RIDERS.keys()))

    # Create and save the new order
    new_order = Order(
        id=uuid.uuid4(),
        store_id=order_data.store_id,
        items=order_data.items,
        status=OrderStatusEnum.PENDING,
        rider_id=assigned_rider_id,
        estimated_delivery_time=eta
    )
    DB_ORDERS[new_order.id] = new_order

    return new_order

@router.get(
    "/orders/{order_id}/status",
    response_model=OrderStatusResponse,
    summary="Get live order status"
)
def get_order_status(order_id: uuid.UUID):
    """
    A dedicated, lightweight endpoint for the frontend to poll for live
    order status and rider location updates.
    """
    order = find_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found."
        )

    rider_location = None
    if order.rider_id and order.status == OrderStatusEnum.OUT_FOR_DELIVERY:
        rider = DB_RIDERS.get(order.rider_id)
        if rider:
            # Simulate rider movement for polling
            rider["location"].lat += random.uniform(-0.001, 0.001)
            rider["location"].lng += random.uniform(-0.001, 0.001)
            rider_location = rider["location"]

    return OrderStatusResponse(
        order_id=order.id,
        status=order.status,
        rider_location=rider_location,
        estimated_delivery_time=order.estimated_delivery_time
    )