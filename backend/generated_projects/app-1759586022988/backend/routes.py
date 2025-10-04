import uuid
from math import sqrt
from typing import List, Optional, Dict

from fastapi import APIRouter, Body, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

# --- Pydantic Models ---
# In a real application, these would be in a separate `models.py` file.

class Store(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    is_active: bool

class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    category: str

class InventoryItem(BaseModel):
    product_id: str
    quantity: int

class Rider(BaseModel):
    id: str
    name: str
    is_available: bool

class OrderItem(BaseModel):
    product_id: str = Field(..., description="The unique identifier of the product.")
    quantity: int = Field(..., gt=0, description="The quantity of the product, must be greater than 0.")

class Order(BaseModel):
    id: str
    store_id: str
    items: List[OrderItem]
    total_price: float
    status: str  # e.g., "processing", "in_transit", "delivered"
    rider_id: Optional[str] = None

# --- Request/Response Models for Endpoints ---

class LocationRequest(BaseModel):
    latitude: float = Field(..., example=34.0522)
    longitude: float = Field(..., example=-118.2437)

class NearestStoreResponse(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float

class OrderCreateRequest(BaseModel):
    store_id: str = Field(..., description="The ID of the store from which to order.")
    items: List[OrderItem]

class OrderItemDetails(BaseModel):
    product: Product
    quantity: int

class OrderDetailsResponse(BaseModel):
    id: str
    status: str
    store_id: str
    total_price: float
    rider: Optional[Rider] = None
    items: List[OrderItemDetails]


# --- In-memory Storage ---
# This acts as a mock database for the purpose of this example.

STORES: Dict[str, Store] = {
    "store-1": Store(id="store-1", name="Downtown QuickMart", latitude=34.0522, longitude=-118.2437, is_active=True),
    "store-2": Store(id="store-2", name="Santa Monica Grocers", latitude=34.0195, longitude=-118.4912, is_active=True),
    "store-3": Store(id="store-3", name="Hollywood Pantry", latitude=34.0928, longitude=-118.3287, is_active=False),
}

PRODUCTS: Dict[str, Product] = {
    "prod-1": Product(id="prod-1", name="Organic Bananas", description="A bunch of fresh organic bananas.", price=1.99, category="fruits"),
    "prod-2": Product(id="prod-2", name="Whole Milk", description="1 gallon of whole milk.", price=3.49, category="dairy"),
    "prod-3": Product(id="prod-3", name="Kettle Chips", description="Sea salt flavor.", price=2.99, category="snacks"),
    "prod-4": Product(id="prod-4", name="Sparkling Water", description="12oz can of lime sparkling water.", price=1.25, category="drinks"),
    "prod-5": Product(id="prod-5", name="Avocado", description="A single ripe avocado.", price=1.50, category="fruits"),
}

INVENTORY: Dict[str, Dict[str, int]] = {
    "store-1": {
        "prod-1": 100,
        "prod-2": 50,
        "prod-3": 75,
        "prod-4": 0,  # Out of stock
        "prod-5": 20,
    },
    "store-2": {
        "prod-1": 80,
        "prod-2": 40,
        "prod-3": 150,
        "prod-4": 100,
        "prod-5": 60,
    },
}

RIDERS: Dict[str, Rider] = {
    "rider-1": Rider(id="rider-1", name="Alex", is_available=True),
    "rider-2": Rider(id="rider-2", name="Maria", is_available=False),
    "rider-3": Rider(id="rider-3", name="John", is_available=True),
}

ORDERS: Dict[str, Order] = {}


# --- API Router ---

router = APIRouter(prefix="/api/v1")


# --- Helper Functions ---

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """A simple Euclidean distance calculation for demonstration."""
    return sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)


# --- Route Implementations ---

@router.post(
    "/stores/locate",
    response_model=NearestStoreResponse,
    summary="Find Nearest Store",
    description="Takes latitude/longitude and returns the closest active dark store.",
)
def locate_nearest_store(location: LocationRequest = Body(...)):
    """
    Finds the nearest active dark store based on the provided GPS coordinates.

    - Iterates through all active stores.
    - Calculates the distance to each.
    - Returns the store with the minimum distance.
    - Raises a 404 error if no active stores are found.
    """
    active_stores = [store for store in STORES.values() if store.is_active]
    if not active_stores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active stores available at the moment.",
        )

    nearest_store = min(
        active_stores,
        key=lambda store: calculate_distance(
            location.latitude, location.longitude, store.latitude, store.longitude
        ),
    )

    return nearest_store


@router.get(
    "/stores/{storeId}/products",
    response_model=List[Product],
    summary="Get Products by Store",
    description="Retrieves a paginated list of available products for a specific store, with optional filtering.",
)
def get_store_products(
    storeId: str = Path(..., description="The ID of the store to retrieve products from."),
    category: Optional[str] = Query(None, description="Filter products by category (e.g., 'snacks')."),
    search: Optional[str] = Query(None, description="Search for products by name or description."),
    skip: int = Query(0, ge=0, description="Number of items to skip for pagination."),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return per page."),
):
    """
    Retrieves available products for a given store with support for filtering and pagination.

    - Validates the `storeId`.
    - Filters products based on availability in the store's inventory.
    - Applies optional category and text search filters.
    - Returns a paginated list of products.
    """
    if storeId not in STORES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Store with ID '{storeId}' not found.")

    store_inventory = INVENTORY.get(storeId, {})
    available_product_ids = {pid for pid, qty in store_inventory.items() if qty > 0}

    # Start with all products that are in stock
    results = [PRODUCTS[pid] for pid in available_product_ids if pid in PRODUCTS]

    # Apply filters
    if category:
        results = [p for p in results if p.category.lower() == category.lower()]
    if search:
        search_term = search.lower()
        results = [p for p in results if search_term in p.name.lower() or search_term in p.description.lower()]

    # Apply pagination
    return results[skip : skip + limit]


@router.post(
    "/orders",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Order",
    description="Creates an order after validating stock, processing a mock payment, and assigning a rider.",
)
def create_order(order_request: OrderCreateRequest = Body(...)):
    """
    Creates a new order.

    - Validates store and product IDs.
    - Checks for sufficient stock for all items.
    - Calculates total price.
    - "Processes" payment and assigns an available rider.
    - Updates inventory and creates the order record.
    - Raises 400 or 404 errors for invalid data or stock issues.
    """
    store_id = order_request.store_id
    if store_id not in STORES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Store with ID '{store_id}' not found.")

    store_inventory = INVENTORY.get(store_id, {})
    total_price = 0.0

    # 1. Validate all items and calculate total price
    for item in order_request.items:
        product = PRODUCTS.get(item.product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID '{item.product_id}' not found.")

        available_stock = store_inventory.get(item.product_id, 0)
        if available_stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'. Requested: {item.quantity}, Available: {available_stock}.",
            )
        total_price += product.price * item.quantity

    # 2. "Process Payment" (mock)
    print(f"Processing payment of ${total_price:.2f}...")

    # 3. Assign Rider
    available_rider = next((rider for rider in RIDERS.values() if rider.is_available), None)
    if not available_rider:
        # In a real app, this might queue the order instead of failing
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No available riders at the moment.")

    # 4. Update inventory and create order (atomic operation in a real DB)
    for item in order_request.items:
        store_inventory[item.product_id] -= item.quantity

    available_rider.is_available = False # Mark rider as busy

    new_order = Order(
        id=f"order-{uuid.uuid4()}",
        store_id=store_id,
        items=order_request.items,
        total_price=round(total_price, 2),
        status="processing",
        rider_id=available_rider.id,
    )
    ORDERS[new_order.id] = new_order

    return new_order


@router.get(
    "/orders/{orderId}",
    response_model=OrderDetailsResponse,
    summary="Get Order Details",
    description="Fetches the complete details of a specific order, including line items and rider info.",
)
def get_order(orderId: str = Path(..., description="The unique ID of the order to retrieve.")):
    """
    Fetches the details for a specific order by its ID.

    - Looks up the order.
    - Resolves product and rider IDs to their full objects for a detailed response.
    - Raises a 404 error if the order ID is not found.
    """
    order = ORDERS.get(orderId)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with ID '{orderId}' not found.")

    # Build the detailed response
    detailed_items = []
    for item in order.items:
        product = PRODUCTS.get(item.product_id)
        if product: # Should always be true if data is consistent
            detailed_items.append(OrderItemDetails(product=product, quantity=item.quantity))

    rider = RIDERS.get(order.rider_id) if order.rider_id else None

    return OrderDetailsResponse(
        id=order.id,
        status=order.status,
        store_id=order.store_id,
        total_price=order.total_price,
        rider=rider,
        items=detailed_items,
    )