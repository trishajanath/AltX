from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional, Dict

# In a real application, these models would be in a separate `models.py` file.
# For this self-contained example, we are assuming they are imported from `.models`.
# from . import models
# --- Start of assumed models.py content ---
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str

class UserCreate(BaseModel):
    username: str
    password: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category: str
    dietary_tags: List[str]
# --- End of assumed models.py content ---


# Security imports for password hashing and JWT
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

# --- In-Memory "Database" ---

# For storing users: {username: UserInDB}
db_users: Dict[str, UserInDB] = {}
# For auto-incrementing user IDs
user_id_counter = 1

# For storing products
db_products: List[Product] = [
    Product(id=1, name="Organic Apples", description="Crisp and juicy organic apples.", price=2.99, category="Fruits", dietary_tags=["organic", "vegan", "gluten-free"]),
    Product(id=2, name="Whole Wheat Bread", description="Freshly baked whole wheat bread.", price=4.50, category="Bakery", dietary_tags=["vegetarian"]),
    Product(id=3, name="Almond Milk", description="Unsweetened almond milk.", price=3.75, category="Dairy Alternatives", dietary_tags=["vegan", "dairy-free", "gluten-free"]),
    Product(id=4, name="Grass-fed Steak", description="Premium quality grass-fed beef steak.", price=15.99, category="Meat", dietary_tags=["gluten-free"]),
    Product(id=5, name="Quinoa Salad", description="Healthy and delicious pre-made quinoa salad.", price=7.99, category="Prepared Foods", dietary_tags=["vegan", "gluten-free"]),
    Product(id=6, name="Cheddar Cheese", description="Sharp cheddar cheese block.", price=6.25, category="Dairy", dietary_tags=["vegetarian", "gluten-free"]),
]


# --- Security Configuration & Helpers ---

# In a real app, load this from environment variables for security.
SECRET_KEY = "a_very_secret_key_that_should_be_in_env_vars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- APIRouter Initialization ---

router = APIRouter(
    prefix="/api/v1"
)


# --- Authentication Endpoints ---

@router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED, summary="Create a new user account.")
def register_user(user_in: UserCreate):
    """
    Create a new user account.

    - **username**: The desired username (must be unique).
    - **password**: The user's password.
    """
    if user_in.username in db_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    global user_id_counter
    hashed_password = get_password_hash(user_in.password)
    
    new_user = UserInDB(
        id=user_id_counter,
        username=user_in.username,
        hashed_password=hashed_password
    )
    
    db_users[user_in.username] = new_user
    user_id_counter += 1
    
    return User(id=new_user.id, username=new_user.username)


@router.post("/auth/token", response_model=Token, summary="Authenticate a user and return a JWT access token.")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate with username and password to get an access token.

    This uses the OAuth2 Password Flow and expects form data (`application/x-www-form-urlencoded`).
    """
    user = db_users.get(form_data.username)
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


# --- Product Endpoints ---

@router.get("/products", response_model=List[Product], summary="Retrieve a paginated list of products.")
def get_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    dietary_tags: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    """
    Retrieve a list of products with optional filtering and pagination.

    - **search**: Filter products by a search term in name or description.
    - **category**: Filter products by category.
    - **dietary_tags**: Filter products by a comma-separated list of tags (e.g., "vegan,gluten-free").
    - **skip**: Number of items to skip for pagination.
    - **limit**: Maximum number of items to return.
    """
    results = db_products

    if search:
        results = [
            p for p in results 
            if search.lower() in p.name.lower() or search.lower() in p.description.lower()
        ]

    if category:
        results = [p for p in results if p.category.lower() == category.lower()]

    if dietary_tags:
        required_tags = {tag.strip().lower() for tag in dietary_tags.split(',')}
        results = [
            p for p in results 
            if required_tags.issubset({tag.lower() for tag in p.dietary_tags})
        ]

    return results[skip : skip + limit]


@router.get("/products/{product_id}", response_model=Product, summary="Get detailed information for a single product.")
def get_product_by_id(product_id: int):
    """
    Get detailed information for a single product by its unique ID.
    """
    product = next((p for p in db_products if p.id == product_id), None)
    
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )
        
    return product