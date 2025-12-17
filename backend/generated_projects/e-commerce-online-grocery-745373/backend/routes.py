from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional

# In a real application, these models would be in a separate 'models.py' file.
# To make this a single, runnable file, we define them here.
# If you have a models.py, change the import to: from .models import ...
from pydantic import BaseModel

# --- Models (normally in models.py) ---

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category: str
    on_sale: bool

class User(BaseModel):
    id: int
    username: str

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# For JWT handling (in a real app, install with 'pip install python-jose[cryptography]')
from jose import JWTError, jwt
from datetime import datetime, timedelta

# --- In-Memory Database ---

# A simple list to store user data. In a real app, use a proper database.
# Note: Storing plain text passwords is a major security risk.
# Use a library like passlib to hash passwords.
db_users = []
next_user_id = 1

# A simple list to store product data.
db_products = [
    {"id": 1, "name": "Organic Milk", "description": "Fresh whole milk from grass-fed cows.", "price": 3.99, "category": "Dairy", "on_sale": True},
    {"id": 2, "name": "Sourdough Bread", "description": "Artisanal sourdough loaf.", "price": 5.49, "category": "Bakery", "on_sale": False},
    {"id": 3, "name": "Cheddar Cheese", "description": "Aged sharp cheddar cheese block.", "price": 7.29, "category": "Dairy", "on_sale": True},
    {"id": 4, "name": "Granny Smith Apples", "description": "A bag of crisp and tart apples.", "price": 4.99, "category": "Produce", "on_sale": False},
    {"id": 5, "name": "Skim Milk", "description": "Low-fat skim milk.", "price": 3.49, "category": "Dairy", "on_sale": False},
]

# --- JWT Configuration ---
# In a real app, load these from environment variables.
SECRET_KEY = "a_very_secret_key_that_should_be_in_env_vars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Helper Functions ---

def get_user(username: str):
    """Helper to find a user by username in the in-memory DB."""
    for user in db_users:
        if user["username"] == username:
            return user
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Helper to create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- APIRouter Setup ---
# All routes in this file will be prefixed with /api/v1
router = APIRouter(
    prefix="/api/v1",
    tags=["API v1"]
)


# --- Authentication Endpoints ---

@router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register_user(user_in: UserCreate):
    """
    Create a new user account.
    - Checks if the username already exists.
    - Stores the new user in the in-memory database.
    - **Note**: Passwords are not hashed in this example for simplicity.
      In a real-world application, **always hash passwords**.
    """
    if get_user(user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    global next_user_id
    # In a real app, hash the password here using passlib
    new_user = {
        "id": next_user_id,
        "username": user_in.username,
        "hashed_password": user_in.password + "_fake_hash"
    }
    db_users.append(new_user)
    next_user_id += 1
    
    # Return the user data without the password
    return User(id=new_user["id"], username=new_user["username"])


@router.post("/auth/token", response_model=Token, tags=["Authentication"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return a JWT access token.
    - Takes username and password from a form body.
    - Verifies credentials against the in-memory database.
    - Returns a JWT token on success.
    """
    user = get_user(form_data.username)
    # In a real app, use a secure password verification function (e.g., passlib.verify)
    if not user or (user["hashed_password"] != form_data.password + "_fake_hash"):
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


# --- Product Endpoints ---

@router.get("/products", response_model=List[Product], tags=["Products"])
def get_products(
    category: Optional[str] = None,
    on_sale: Optional[bool] = None,
    q: Optional[str] = None
):
    """
    Retrieve a list of products with optional filtering and searching.
    - **category**: Filter products by category name (case-insensitive).
    - **on_sale**: Filter products that are currently on sale.
    - **q**: Search for a string in product names and descriptions (case-insensitive).
    
    Example: `/api/v1/products?category=Dairy&on_sale=true&q=milk`
    """
    results = db_products.copy()

    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]

    if on_sale is not None:
        results = [p for p in results if p["on_sale"] == on_sale]

    if q:
        q_lower = q.lower()
        results = [
            p for p in results 
            if q_lower in p["name"].lower() or q_lower in p["description"].lower()
        ]
        
    return results


@router.get("/products/{product_id}", response_model=Product, tags=["Products"])
def get_product_by_id(product_id: int):
    """
    Get detailed information for a single product by its ID.
    - Returns the product details if found.
    - Returns a 404 Not Found error if the product ID does not exist.
    """
    product = next((p for p in db_products if p["id"] == product_id), None)
    
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
        
    return product