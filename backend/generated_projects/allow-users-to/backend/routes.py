import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt

# In a real application, these models would be in a separate `models.py` file.
# To fulfill the "Python code only" requirement, they are defined here for context.
# --- Start of Faux models.py ---
from pydantic import BaseModel, Field, EmailStr

class Product(BaseModel):
    id: int
    name: str
    category: str
    price: float
    description: Optional[str] = None

class User(BaseModel):
    id: int
    email: EmailStr
    full_name: str

class UserInDB(User):
    # This model is used for internal storage and includes the hashed password
    hashed_password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
# --- End of Faux models.py ---


# --- Configuration ---
# In a real app, load these from environment variables or a config file.
SECRET_KEY = "a_very_secret_key_that_should_be_in_env_vars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- In-Memory Database ---
# This is a simple in-memory storage. In a real application, you would use a database.
# NOTE: For simplicity, we are storing passwords as plain text.
# In a real-world scenario, ALWAYS hash passwords using a library like passlib.
db_users: dict[int, UserInDB] = {
    1: UserInDB(id=1, email="test@example.com", full_name="Test User", hashed_password="password123"),
}
next_user_id = 2

db_products: List[Product] = [
    Product(id=1, name="Organic Whole Milk", category="Dairy", price=3.99, description="Fresh organic whole milk from grass-fed cows."),
    Product(id=2, name="Cheddar Cheese Block", category="Dairy", price=5.49, description="A sharp and tangy 8oz cheddar cheese block."),
    Product(id=3, name="Artisan Sourdough Bread", category="Bakery", price=4.29, description="Handmade, crusty sourdough bread loaf."),
    Product(id=4, name="Granny Smith Apples", category="Produce", price=0.79, description="Crisp and tart green apples, sold per piece."),
    Product(id=5, name="Skim Milk", category="Dairy", price=3.79, description="Fat-free skim milk, 1 gallon."),
    Product(id=6, name="Gourmet Ground Coffee", category="Pantry", price=12.99, description="Rich and aromatic dark roast coffee beans."),
]

# --- APIRouter Setup ---
router = APIRouter(
    prefix="/api/v1",
    tags=["api-v1"],
)

# --- Helper Functions ---
def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Find a user in the in-memory DB by email."""
    for user in db_users.values():
        if user.email == email:
            return user
    return None

def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user by checking email and password."""
    user = get_user_by_email(email)
    if not user:
        return None
    # Simple plain text password check. DO NOT use in production.
    if user.hashed_password != password:
        return None
    return user

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


# --- Authentication Routes ---

@router.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    User login. Takes email and password, returns a JWT access token.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
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
async def register_new_user(user_in: UserCreate):
    """
    New user registration. Takes email, password, and full name.
    """
    db_user = get_user_by_email(user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    global next_user_id
    new_user = UserInDB(
        id=next_user_id,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=user_in.password, # Again, hash this in a real app!
    )
    db_users[next_user_id] = new_user
    next_user_id += 1
    
    # Return a User model, which doesn't include the password
    return User.model_validate(new_user)


# --- Product Routes ---

@router.get("/products", response_model=List[Product], tags=["Products"])
async def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by_price: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """
    Fetch a paginated list of products.
    Supports filtering by category, searching by name, and sorting by price.
    """
    results = list(db_products)

    # Filtering by category
    if category:
        results = [p for p in results if p.category.lower() == category.lower()]

    # Searching by name
    if search:
        results = [p for p in results if search.lower() in p.name.lower()]

    # Sorting by price
    if sort_by_price:
        if sort_by_price.lower() == 'asc':
            results.sort(key=lambda p: p.price)
        elif sort_by_price.lower() == 'desc':
            results.sort(key=lambda p: p.price, reverse=True)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid value for sort_by_price. Use 'asc' or 'desc'."
            )

    # Pagination
    return results[skip : skip + limit]


@router.get("/products/{product_id}", response_model=Product, tags=["Products"])
async def get_product_by_id(product_id: int):
    """
    Retrieve detailed information for a single product by its ID.
    """
    product = next((p for p in db_products if p.id == product_id), None)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    return product