# routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional, Annotated
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import uuid

# --- Pydantic Models ---
# In a real application, these models would be in a separate 'models.py' file.

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str

class Product(BaseModel):
    id: int
    name: str
    category: str
    price: float

class OrderItem(BaseModel):
    product_id: int
    quantity: int

class OrderIn(BaseModel):
    items: List[OrderItem]

class Order(BaseModel):
    id: str
    owner: str
    items: List[OrderItem]
    status: str
    created_at: datetime


# --- In-Memory Storage ---
# This simulates a database for demonstration purposes.

db_users = {
    "user1": {
        "username": "user1",
        # In a real app, use a secure hashing library like passlib
        # e.g., "hashed_password": pwd_context.hash("password123")
        "password": "password123"
    },
    "user2": {
        "username": "user2",
        "password": "password456"
    }
}

db_products = [
    Product(id=1, name="Laptop", category="Electronics", price=1200.00),
    Product(id=2, name="Smartphone", category="Electronics", price=800.00),
    Product(id=3, name="Coffee Mug", category="Kitchenware", price=15.50),
    Product(id=4, name="Notebook", category="Stationery", price=5.25),
    Product(id=5, name="Wireless Mouse", category="Electronics", price=50.00),
]

db_orders: List[Order] = []


# --- Security and JWT Configuration ---
# NOTE: In a real app, use environment variables for secrets.
SECRET_KEY = "a_very_secret_key_that_should_be_in_env_vars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db_users.get(token_data.username)
    if user is None:
        raise credentials_exception
    return User(username=user["username"])


# --- API Routers ---

# Router for authentication
auth_router = APIRouter(
    tags=["Authentication"]
)

# Router for main API with /api/v1 prefix
api_router = APIRouter(
    prefix="/api/v1",
    tags=["API"],
    # You can add dependencies that apply to all routes in this router
    # dependencies=[Depends(get_current_user)]
)


# --- Authentication Endpoints ---

@auth_router.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    User login and get JWT token.
    - Takes username and password from a form body.
    - Verifies credentials against the in-memory user database.
    - Returns a JWT access token on success.
    """
    user = db_users.get(form_data.username)
    # In a real app, you would compare hashed passwords
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- API Endpoints ---

@api_router.get("/products", response_model=List[Product])
async def list_products(search: Optional[str] = None, category: Optional[str] = None):
    """
    List all available products with search and filtering.
    - `search`: A string to search for in product names (case-insensitive).
    - `category`: A string to filter products by category (case-insensitive).
    """
    results = db_products
    if search:
        results = [p for p in results if search.lower() in p.name.lower()]
    if category:
        results = [p for p in results if category.lower() == p.category.lower()]
    return results

@api_router.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderIn,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Create a new order from the user's cart.
    - Requires authentication.
    - Validates that all product IDs in the order exist.
    - Creates and stores a new order associated with the current user.
    """
    # Validate product IDs
    product_ids = {p.id for p in db_products}
    for item in order_in.items:
        if item.product_id not in product_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with ID {item.product_id} not found."
            )

    new_order = Order(
        id=str(uuid.uuid4()),
        owner=current_user.username,
        items=order_in.items,
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    db_orders.append(new_order)
    return new_order

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order_details(
    order_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get the status and details of a specific order.
    - Requires authentication.
    - Ensures the user can only access their own orders.
    """
    order = next((o for o in db_orders if o.id == order_id), None)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found."
        )

    if order.owner != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this order."
        )

    return order

# To use these routers in your main application file (e.g., main.py):
#
# from fastapi import FastAPI
# from . import routes
#
# app = FastAPI()
#
# app.include_router(routes.auth_router)
# app.include_router(routes.api_router)