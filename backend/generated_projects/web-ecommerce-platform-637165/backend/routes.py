import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

# --- Pydantic Models ---
# In a real application, these would be in a separate 'models.py' file.

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool = True

    class Config:
        orm_mode = True

class UserInDB(User):
    hashed_password: str

class Product(BaseModel):
    id: int
    name: str
    category: str
    price: float
    description: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# --- In-Memory Storage ---
# A simple in-memory "database" for demonstration purposes.

fake_users_db = {
    1: {
        "id": 1,
        "email": "user1@example.com",
        "full_name": "Alice Smith",
        "hashed_password": "fake_hashed_password_1", # In a real app, use a strong hash
        "is_active": True,
    },
    2: {
        "id": 2,
        "email": "user2@example.com",
        "full_name": "Bob Johnson",
        "hashed_password": "fake_hashed_password_2",
        "is_active": True,
    },
}

fake_products_db = [
    Product(id=1, name="Laptop Pro", category="electronics", price=1200.00, description="A powerful laptop for professionals."),
    Product(id=2, name="Smartphone X", category="electronics", price=800.50, description="The latest smartphone with a great camera."),
    Product(id=3, name="Classic T-Shirt", category="apparel", price=25.00, description="A comfortable 100% cotton t-shirt."),
    Product(id=4, name="Running Shoes", category="footwear", price=100.00, description="Lightweight shoes for running enthusiasts."),
    Product(id=5, name="Coffee Maker", category="home_goods", price=75.25, description="Brews the perfect cup of coffee every morning."),
    Product(id=6, name="Wireless Headphones", category="electronics", price=150.00, description="Noise-cancelling over-ear headphones."),
]

# --- Security & JWT Configuration ---

# Generate a secret key with: openssl rand -hex 32
SECRET_KEY = os.environ.get("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# --- Helper Functions ---

def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Retrieve a user from the DB by email."""
    for user_data in fake_users_db.values():
        if user_data["email"] == email:
            return UserInDB(**user_data)
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Dependency to get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return User(**user.dict())


# --- APIRouter Setup ---
# All routes will be prefixed with /api/v1
router = APIRouter(prefix="/api/v1")


# --- Authentication Endpoints ---

@router.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    User login. Takes email and password, returns a JWT access token.
    
    Note: For this demo, password verification is a simple string comparison.
    In a real application, use a library like passlib for hashing and verification.
    """
    user = get_user_by_email(form_data.username)
    # Simple password check (NOT FOR PRODUCTION)
    if not user or user.hashed_password != f"fake_hashed_password_{user.id}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register_user(user_in: UserCreate):
    """
    Create a new user account.
    """
    if get_user_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    new_user_id = max(fake_users_db.keys()) + 1
    # Simple password "hashing" (NOT FOR PRODUCTION)
    hashed_password = f"fake_hashed_password_{new_user_id}"
    
    new_user_data = {
        "id": new_user_id,
        "email": user_in.email,
        "full_name": user_in.full_name,
        "hashed_password": hashed_password,
        "is_active": True,
    }
    
    fake_users_db[new_user_id] = new_user_data
    return User(**new_user_data)


# --- User Endpoints ---

@router.get("/users/me", response_model=User, tags=["Users"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get the profile information of the currently authenticated user.
    """
    return current_user


# --- Product Endpoints ---

@router.get("/products", response_model=List[Product], tags=["Products"])
async def get_products(
    category: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    """
    Retrieve a paginated list of products.
    Supports filtering by 'category' and searching by 'q' query parameters.
    """
    results = fake_products_db

    if category:
        results = [p for p in results if p.category.lower() == category.lower()]

    if q:
        query_lower = q.lower()
        results = [
            p for p in results 
            if query_lower in p.name.lower() or (p.description and query_lower in p.description.lower())
        ]

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No products found matching the criteria."
        )

    return results[skip : skip + limit]


# --- Cart Models ---

class CartItem(BaseModel):
    product_id: int
    quantity: int
    
class Cart(BaseModel):
    user_id: int
    items: List[CartItem] = []
    
class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = 1

class PaymentRequest(BaseModel):
    cart_total: float
    payment_method: str  # "stripe", "paypal", etc.
    payment_details: dict

# --- In-Memory Cart Storage ---
fake_carts_db = {}  # user_id -> Cart

# --- Cart Endpoints ---

@router.post("/cart/add", tags=["Cart"])
async def add_to_cart(
    request: AddToCartRequest,
    current_user: User = Depends(get_current_user)
):
    """Add an item to the user's cart."""
    # Check if product exists
    product = next((p for p in fake_products_db if p.id == request.product_id), None)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Initialize cart if doesn't exist
    if current_user.id not in fake_carts_db:
        fake_carts_db[current_user.id] = Cart(user_id=current_user.id, items=[])
    
    cart = fake_carts_db[current_user.id]
    
    # Check if item already in cart
    existing_item = next((item for item in cart.items if item.product_id == request.product_id), None)
    if existing_item:
        existing_item.quantity += request.quantity
    else:
        cart.items.append(CartItem(product_id=request.product_id, quantity=request.quantity))
    
    return {
        "success": True,
        "message": f"Added {request.quantity} x {product.name} to cart",
        "cart_items": len(cart.items)
    }

@router.get("/cart", tags=["Cart"])
async def get_cart(current_user: User = Depends(get_current_user)):
    """Get the current user's cart."""
    if current_user.id not in fake_carts_db:
        return {"items": [], "total": 0.0}
    
    cart = fake_carts_db[current_user.id]
    cart_details = []
    total = 0.0
    
    for item in cart.items:
        product = next((p for p in fake_products_db if p.id == item.product_id), None)
        if product:
            item_total = product.price * item.quantity
            total += item_total
            cart_details.append({
                "product": product,
                "quantity": item.quantity,
                "item_total": item_total
            })
    
    return {
        "items": cart_details,
        "total": round(total, 2),
        "item_count": len(cart.items)
    }

@router.delete("/cart/item/{product_id}", tags=["Cart"])
async def remove_from_cart(
    product_id: int,
    current_user: User = Depends(get_current_user)
):
    """Remove an item from the cart."""
    if current_user.id not in fake_carts_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    
    cart = fake_carts_db[current_user.id]
    cart.items = [item for item in cart.items if item.product_id != product_id]
    
    return {"success": True, "message": "Item removed from cart"}

@router.post("/cart/clear", tags=["Cart"])
async def clear_cart(current_user: User = Depends(get_current_user)):
    """Clear all items from the cart."""
    if current_user.id in fake_carts_db:
        fake_carts_db[current_user.id].items = []
    
    return {"success": True, "message": "Cart cleared"}

# --- Payment Endpoints ---

@router.post("/payment/process", tags=["Payment"])
async def process_payment(
    payment_request: PaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Process a payment (mock implementation).
    In a real app, integrate with Stripe, PayPal, or other payment providers.
    """
    
    # Get cart to validate total
    if current_user.id not in fake_carts_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty cart")
    
    cart = fake_carts_db[current_user.id]
    if not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty cart")
    
    # Calculate actual total
    actual_total = 0.0
    for item in cart.items:
        product = next((p for p in fake_products_db if p.id == item.product_id), None)
        if product:
            actual_total += product.price * item.quantity
    
    actual_total = round(actual_total, 2)
    
    # Validate payment amount
    if abs(payment_request.cart_total - actual_total) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment total mismatch. Expected: ${actual_total}, Received: ${payment_request.cart_total}"
        )
    
    # Mock payment processing
    if payment_request.payment_method.lower() == "stripe":
        # In real implementation: stripe.PaymentIntent.create(...)
        payment_id = f"pi_mock_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        status_result = "succeeded"
    elif payment_request.payment_method.lower() == "paypal":
        # In real implementation: PayPal SDK integration
        payment_id = f"paypal_mock_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        status_result = "completed"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported payment method"
        )
    
    # Clear cart after successful payment
    fake_carts_db[current_user.id].items = []
    
    return {
        "success": True,
        "payment_id": payment_id,
        "status": status_result,
        "amount": actual_total,
        "message": "Payment processed successfully",
        "order_id": f"order_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    }

@router.get("/payment/methods", tags=["Payment"])
async def get_payment_methods():
    """Get available payment methods."""
    return {
        "methods": [
            {
                "id": "stripe",
                "name": "Credit Card (Stripe)",
                "description": "Pay with credit or debit card",
                "enabled": True
            },
            {
                "id": "paypal",
                "name": "PayPal",
                "description": "Pay with your PayPal account",
                "enabled": True
            }
        ]
    }