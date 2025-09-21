```python
import uuid
from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime

from .models import (
    Restaurant, MenuItem, OrderCreateRequest, OrderResponse, OrderStatus, 
    RestaurantListResponse, OrderItemResponse
)

#  In-Memory Database Simulation 
# In a real application, this data would come from a database (e.g., PostgreSQL, MongoDB).
# For this example, we simulate it with in-memory Python objects.

DB_RESTAURANTS: dict[uuid.UUID, Restaurant] = {}
DB_ORDERS: dict[uuid.UUID, OrderResponse] = {}

def populate_mock_data():
    """Initializes the in-memory 'database' with some sample data."""
    # Restaurant 1: The Gourmet Kitchen
    gourmet_menu = [
        MenuItem(id=uuid.uuid4(), name="Truffle Risotto", description="Creamy Arborio rice with black truffle and Parmesan cheese.", price=22.50, image_url="https://example.com/images/risotto.jpg"),
        MenuItem(id=uuid.uuid4(), name="Seared Scallops", description="Pan-seared scallops with a lemon-butter sauce.", price=28.00, image_url="https://example.com/images/scallops.jpg"),
    ]
    gourmet_id = uuid.uuid4()
    DB_RESTAURANTS[gourmet_id] = Restaurant(
        id=gourmet_id, 
        name="The Gourmet Kitchen", 
        cuisine_type="Italian", 
        address="123 Fine Dining Rd, Flavor Town", 
        rating=4.8,
        menu=gourmet_menu
    )

    # Restaurant 2: Spice Route
    spice_menu = [
        MenuItem(id=uuid.uuid4(), name="Chicken Tikka Masala", description="Grilled chicken chunks in a spicy, creamy tomato sauce.", price=16.00, image_url="https://example.com/images/tikka.jpg"),
        MenuItem(id=uuid.uuid4(), name="Vegetable Biryani", description="Aromatic basmati rice cooked with mixed vegetables and spices.", price=14.50, image_url="https://example.com/images/biryani.jpg"),
        MenuItem(id=uuid.uuid4(), name="Garlic Naan", description="Soft Indian bread with garlic and butter.", price=4.00, image_url="https://example.com/images/naan.jpg"),
    ]
    spice_id = uuid.uuid4()
    DB_RESTAURANTS[spice_id] = Restaurant(
        id=spice_id, 
        name="Spice Route", 
        cuisine_type="Indian", 
        address="456 Curry Lane, Spice City", 
        rating=4.5,
        menu=spice_menu
    )

# Call this function once when the module is loaded to set up our data
populate_mock_data()

#  API Router Setup 
router = APIRouter()

#  Helper Functions 
def find_restaurant_by_id(restaurant_id: uuid.UUID) -> Restaurant:
    """Finds a restaurant by its ID or raises HTTPException."""
    restaurant = DB_RESTAURANTS.get(restaurant_id)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID {restaurant_id} not found."
        )
    return restaurant

#  API Endpoints 

@router.get(
    "/restaurants",
    response_model=List[RestaurantListResponse],
    summary="List all available restaurants",
    description="Returns a list of all restaurants, excluding their detailed menus for brevity."
)
async def list_restaurants():
    """
    Retrieves a list of all restaurants.
    The response is a simplified model to keep the payload small.
    """
    return list(DB_RESTAURANTS.values())

@router.get(
    "/restaurants/{restaurant_id}",
    response_model=Restaurant,
    summary="Get details of a specific restaurant",
    description="Fetches the full details of a restaurant, including its complete menu."
)
async def get_restaurant_details(restaurant_id: uuid.UUID):
    """
    Retrieves detailed information for a single restaurant by its UUID.
    Returns a 404 error if the restaurant ID does not exist.
    """
    return find_restaurant_by_id(restaurant_id)

@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new food order",
    description="Places a new order for a given restaurant and list of menu items."
)
async def create_order(order_request: OrderCreateRequest):
    """
    Creates a new order. The business logic here involves:
    1. Validating the restaurant exists.
    2. Validating all menu items in the order exist for that restaurant.
    3. Calculating the total price.
    4. Creating and 'storing' the order.
    """
    restaurant = find_restaurant_by_id(order_request.restaurant_id)
    
    total_amount = 0.0
    order_items_response = []
    
    # Create a quick lookup map for menu item IDs to their objects for efficiency
    menu_item_map = {item.id: item for item in restaurant.menu}

    for item_order in order_request.items:
        menu_item = menu_item_map.get(item_order.menu_item_id)
        
        if not menu_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Menu item with ID {item_order.menu_item_id} not found in restaurant {restaurant.name}."
            )
        
        total_amount += menu_item.price * item_order.quantity
        order_items_response.append(
            OrderItemResponse(
                menu_item_name=menu_item.name,
                quantity=item_order.quantity,
                price_per_item=menu_item.price
            )
        )

    new_order = OrderResponse(
        id=uuid.uuid4(),
        restaurant_id=restaurant.id,
        items=order_items_response,
        total_amount=round(total_amount, 2),
        status=OrderStatus.PLACED,
        created_at=datetime.utcnow()
    )

    DB_ORDERS[new_order.id] = new_order
    return new_order

@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get the status of an order",
    description="Retrieves the details and current status of a specific order by its ID."
)
async def get_order_status(order_id: uuid.UUID):
    """
    Fetches an order by its UUID.
    Returns a 404 error if the order ID is not found.
    """
    order = DB_ORDERS.get(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found."
        )
    return order
```