from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# --- Pydantic Models (This section would typically be in a 'models.py' file) ---
# This simulates the 'from . import models' requirement.

class Product(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None

class OrderItem(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    items: List[OrderItem]

class Order(BaseModel):
    id: int
    user_id: str
    items: List[OrderItem]
    total_price: float
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str


# --- In-Memory Storage (Simulating a Database) ---

# Products database
db_products = {
    1: {"id": 1, "name": "Laptop Pro", "price": 1200.00, "description": "A powerful and sleek laptop."},
    2: {"id": 2, "name": "Wireless Mouse", "price": 25.50, "description": "An ergonomic wireless mouse."},
    3: {"id": 3, "name": "Mechanical Keyboard", "price": 75.00, "description": "A backlit mechanical keyboard."},
}

# Users database with hashed passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db_users = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": pwd_context.hash("secretpassword"),
        "disabled": False,
    }
}

# Orders database
db_orders: List[Order] = []
next_order_id = 1


# --- Security & JWT Configuration ---

SECRET_KEY = "a_very_secret_key_that_should_be_in_env_vars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    if username in db_users:
        user_dict = db_users[username]
        return UserInDB(**user_dict)
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
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
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# --- APIRouter Setup ---

router = APIRouter(
    prefix="/api/v1",
    tags=["v1"],
)


# --- Endpoints ---

@router.get("/products", response_model=List[Product], summary="List all available products.")
async def list_products():
    """
    Retrieves a list of all products available in the store.
    """
    return list(db_products.values())

@router.get("/products/{product_id}", response_model=Product, summary="Get details for a single product.")
async def get_product(product_id: int):
    """
    Retrieves detailed information for a specific product by its ID.
    - **product_id**: The integer ID of the product to retrieve.
    """
    product = db_products.get(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.post("/auth/token", response_model=Token, summary="Authenticate a user and return a JWT.")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticates a user with username and password provided in a form.
    Returns a JWT access token upon successful authentication.
    """
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED, summary="Create a new order from the user's cart (requires authentication).")
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_active_user)):
    """
    Creates a new order for the authenticated user.
    - Requires a valid JWT in the 'Authorization: Bearer <token>' header.
    - The request body should contain a list of items with product IDs and quantities.
    """
    global next_order_id
    total_price = 0.0
    
    if not order_data.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create an empty order.")

    # Validate products and calculate total price
    for item in order_data.items:
        product = db_products.get(item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {item.product_id} not found."
            )
        total_price += product["price"] * item.quantity

    # Create and store the new order
    new_order = Order(
        id=next_order_id,
        user_id=current_user.username,
        items=order_data.items,
        total_price=round(total_price, 2),
        created_at=datetime.utcnow()
    )
    db_orders.append(new_order)
    next_order_id += 1
    
    return new_order