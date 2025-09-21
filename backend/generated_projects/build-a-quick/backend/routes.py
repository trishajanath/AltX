```python
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict

from . import models

#  In-Memory Database Simulation 
# In a real application, this data would come from a database (e.g., PostgreSQL).
# For this example, we use simple Python dictionaries to store data.
# The data is populated on application startup in main.py.

db: Dict[str, Dict] = {
    "stores": {},
    "orders": {}
}

# Dependency to get the database. In a real app, this would manage DB sessions.
def get_db():
    return db

#  API Router Setup 
router = APIRouter()

#  Store and Product Endpoints 

@router.get("/stores", response_model=List[models.Store])
async def list_stores(db: Dict = Depends(get_db)):
    """
    
🛡️ **Advanced Security Analysis**
    - **Threat:** Uncontrolled data exposure.
    - **Risk:** Low. In this case, listing public stores is intended. In a more complex system with sensitive store data (e.g., internal performance metrics), this endpoint would need authentication and authorization to ensure only permitted users can access it.
    - **Remediation:** Implement role-based access control (RBAC) using FastAPI's dependency injection system with an authentication scheme (e.g., OAuth2).
    """
    return list(db["stores"].values())

@router.get("/stores/{store_id}/products", response_model=List[models.Product])
async def get_store_products(store_id: uuid.UUID, db: Dict = Depends(get_db)):
    """
    Retrieves the list of products available at a specific store.
    """
    store = db["stores"].get(store_id)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found."
        )
    return store.inventory

#  Order Management Endpoints 

@router.post("/orders", response_model=models.OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_request: models.OrderCreateRequest, db: Dict = Depends(get_db)):
    """
    Creates a new order.

    🔬 **Expert Code Review & Security Analysis:**
    This is a critical business logic endpoint.
    - **Validation:** Pydantic handles input validation (e.g., positive quantities).
    - **Business Logic Vulnerability:** Race Conditions. If two orders for the last item in stock are placed simultaneously, both might pass the stock check before the inventory is updated.
    - **Risk:** High (Inventory mismatch, revenue loss, customer dissatisfaction).
    - **Remediation (Real World):**
        1. **Database Transactions:** Use `SELECT ... FOR UPDATE` in a SQL database to lock the product rows during the transaction.
        2. **Atomic Operations:** Use atomic decrement operations provided by databases like Redis (`DECRBY`) or specific ORM features.
        3. **Optimistic Locking:** Add a `version` number to the product model. The update operation would fail if the version has changed since it was read.
    """
    store = db["stores"].get(order_request.store_id)
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    total_amount = 0.0
    order_items_response: List[models.OrderItemResponse] = []
    
    # Create a mapping of product IDs to product objects for efficient lookups
    store_inventory_map = {p.id: p for p in store.inventory}

    # Verify all items, calculate total, and check stock
    for item in order_request.items:
        product = store_inventory_map.get(item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with ID {item.product_id} not found in this store."
            )
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock_quantity}, Requested: {item.quantity}"
            )
        
        total_amount += product.price * item.quantity
        order_items_response.append(
            models.OrderItemResponse(
                product_id=product.id,
                product_name=product.name,
                quantity=item.quantity,
                price_per_item=product.price
            )
        )

    # All checks passed, now atomically (simulated) update stock
    for item in order_request.items:
        store_inventory_map[item.product_id].stock_quantity -= item.quantity

    # Create and "save" the order
    new_order = models.OrderResponse(
        id=uuid.uuid4(),
        store_id=order_request.store_id,
        user_id=order_request.user_id,
        items=order_items_response,
        total_amount=round(total_amount, 2),
        status=models.OrderStatus.PLACED,
        created_at=datetime.utcnow(),
        estimated_delivery_time=datetime.utcnow() + timedelta(minutes=15)
    )

    db["orders"][new_order.id] = new_order
    return new_order

@router.get("/orders/{order_id}", response_model=models.OrderResponse)
async def get_order_status(order_id: uuid.UUID, db: Dict = Depends(get_db)):
    """
    Retrieves the details and status of a specific order.
    """
    order = db["orders"].get(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found."
        )
    return order

@router.put("/orders/{order_id}/status", response_model=models.OrderResponse)
async def update_order_status(
    order_id: uuid.UUID,
    status_update: models.OrderStatusUpdateRequest,
    db: Dict = Depends(get_db)
):
    """
    Updates the status of an order. In a real app, this would be a protected endpoint
    for delivery personnel or internal systems.
    """
    order = db["orders"].get(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found."
        )
    
    # In a real system, you would have a state machine to validate transitions
    # (e.g., an order cannot go from 'placed' to 'delivered' instantly).
    order.status = status_update.status
    db["orders"][order_id] = order
    return order
```