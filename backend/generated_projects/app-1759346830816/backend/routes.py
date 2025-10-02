from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional

# Assumes models are defined in a sibling 'models.py' file
from .models import (
    User, UserCreate, UserLogin, Token,
    Product,
    Cart, CartItem,
    Order
)

router = APIRouter()

# --- In-Memory Storage ---
db_users = {}
db_products = {
    1: Product(id=1, name="Laptop", price=1200.00, category="Electronics"),
    2: Product(id=2, name="Smartphone", price=800.00, category="Electronics"),
    3: Product(id=3, name="Book: FastAPI Guide", price=49.99, category="Books"),
}
db_carts = {}  # {user_id: Cart}
db_orders = {}  # {user_id: [Order]}
next_user_id = 1
next_order_id = 1

# --- Simulated Authentication Dependency ---
def get_current_user() -> User:
    """A simulated dependency to get the current user. Returns a default user."""
    if 1 not in db_users: # Create a default user if none exist
        default_user = User(id=1, username="testuser", email="test@example.com")
        db_users[1] = default_user
        db_carts[1] = Cart(user_id=1, items=[])
    return db_users[1]

# --- Auth Endpoints ---
@router.post("/api/auth/register", response_model=User, status_code=status.HTTP_201_CREATED, summary="Create a new user account.")
def register_user(user_in: UserCreate):
    global next_user_id
    if any(u.username == user_in.username for u in db_users.values()):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = User(id=next_user_id, **user_in.dict(exclude={"password"}))
    db_users[next_user_id] = new_user
    db_carts[next_user_id] = Cart(user_id=next_user_id, items=[])
    next_user_id += 1
    return new_user

@router.post("/api/auth/login", response_model=Token, summary="Authenticate a user and return a session token (JWT).")
def login(form_data: UserLogin):
    user = next((u for u in db_users.values() if u.username == form_data.username), None)
    if not user: # In a real app, you would also check the password
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return Token(access_token=f"fake-jwt-for-{user.username}", token_type="bearer")

# --- Product Endpoints ---
@router.get("/api/products", response_model=List[Product], summary="Retrieve a list of all products, with support for filtering and pagination.")
def get_products(category: Optional[str] = None, skip: int = 0, limit: int = 10):
    products = list(db_products.values())
    if category:
        products = [p for p in products if p.category.lower() == category.lower()]
    return products[skip : skip + limit]

@router.get("/api/products/{id}", response_model=Product, summary="Retrieve details for a single product by its ID.")
def get_product(id: int):
    product = db_products.get(id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# --- Cart Endpoints ---
@router.get("/api/cart", response_model=Cart, summary="Get the contents of the current user's shopping cart.")
def get_cart(current_user: User = Depends(get_current_user)):
    return db_carts.get(current_user.id, Cart(user_id=current_user.id))

@router.post("/api/cart/items", response_model=Cart, summary="Add a new item to the user's shopping cart or update its quantity.")
def add_or_update_cart_item(item: CartItem, current_user: User = Depends(get_current_user)):
    if item.product_id not in db_products:
        raise HTTPException(status_code=404, detail="Product not found")
    
    cart = db_carts.setdefault(current_user.id, Cart(user_id=current_user.id))
    existing_item = next((i for i in cart.items if i.product_id == item.product_id), None)
    
    if existing_item:
        existing_item.quantity = item.quantity
    else:
        cart.items.append(item)
    return cart

@router.delete("/api/cart/items/{itemId}", response_model=Cart, summary="Remove an item from the user's shopping cart.")
def remove_cart_item(itemId: int, current_user: User = Depends(get_current_user)):
    cart = db_carts.get(current_user.id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    item_to_remove = next((i for i in cart.items if i.product_id == itemId), None)
    if not item_to_remove:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    cart.items.remove(item_to_remove)
    return cart

# --- Order Endpoints ---
@router.post("/api/orders", response_model=Order, status_code=status.HTTP_201_CREATED, summary="Create a new order from the user's cart (checkout process).")
def create_order(current_user: User = Depends(get_current_user)):
    global next_order_id
    cart = db_carts.get(current_user.id)
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cannot create order from empty cart")

    new_order = Order(id=next_order_id, user_id=current_user.id, items=list(cart.items))
    db_orders.setdefault(current_user.id, []).append(new_order)
    cart.items.clear()  # Empty the cart
    next_order_id += 1
    return new_order

@router.get("/api/orders", response_model=List[Order], summary="Retrieve a list of the authenticated user's past orders.")
def get_orders(current_user: User = Depends(get_current_user)):
    return db_orders.get(current_user.id, [])

# --- User Profile Endpoint ---
@router.get("/api/users/me", response_model=User, summary="Get the profile information for the currently authenticated user.")
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user