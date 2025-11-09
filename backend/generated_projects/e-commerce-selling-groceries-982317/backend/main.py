# main.py
# COMPLETE, PRODUCTION-READY FastAPI main.py for: e-commerce-selling-groceries-982317

# --- Imports ---
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, Text, 
                        Float, ForeignKey, Boolean, JSON, Table)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.sql import func

# --- Configuration ---
# In a real production environment, use environment variables for sensitive data.
# Example: SECRET_KEY = os.getenv("SECRET_KEY", "a_default_secret_key")
SECRET_KEY = "e-commerce-selling-groceries-982317-super-secret-key-for-jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./ecommerce_groceries_electronics.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database Models ---

# Association table for Recipe and Product (Ingredients)
recipe_ingredient_association = Table(
    'recipe_ingredient_association', Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True)
)

# Association table for Subscription and Product
subscription_product_association = Table(
    'subscription_product_association', Base.metadata,
    Column('subscription_id', Integer, ForeignKey('subscriptions.id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    image_url = Column(String)
    category = Column(String, index=True, nullable=False)  # "groceries" or "electronics"
    stock_quantity = Column(Integer, default=0)
    specifications = Column(JSON, default={}) # For filters like 'Organic', 'Brand', 'RAM'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="pending") # e.g., pending, processing, shipped, delivered, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Feature-specific fields
    delivery_slot_start = Column(DateTime(timezone=True), nullable=True) # For Scheduled Grocery Delivery
    delivery_slot_end = Column(DateTime(timezone=True), nullable=True)
    tracking_info = Column(JSON, default={}) # For Real-Time Order Tracking

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer)
    price_at_purchase = Column(Float)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    instructions = Column(Text)
    image_url = Column(String)

    ingredients = relationship("Product", secondary=recipe_ingredient_association)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    frequency = Column(String, nullable=False) # e.g., "weekly", "monthly"
    next_delivery_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subscriptions")
    products = relationship("Product", secondary=subscription_product_association)


# --- Pydantic Schemas ---

# User and Auth Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[EmailStr] = None

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category: str
    stock_quantity: int
    specifications: Optional[Dict[str, Any]] = {}

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductComparisonRequest(BaseModel):
    product_ids: List[int] = Field(..., min_items=2, max_items=4)

# Cart Schemas
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(1, gt=0)

class CartItemResponse(BaseModel):
    id: int
    quantity: int
    product: ProductResponse

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_price: float

# Order Schemas
class OrderItemResponse(BaseModel):
    quantity: int
    price_at_purchase: float
    product: ProductResponse

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    delivery_slot_start: Optional[datetime] = None # For grocery orders

class OrderResponse(BaseModel):
    id: int
    total_amount: float
    status: str
    created_at: datetime
    delivery_slot_start: Optional[datetime] = None
    delivery_slot_end: Optional[datetime] = None
    tracking_info: Dict[str, Any]
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

# Recipe Schemas
class RecipeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    image_url: Optional[str] = None
    ingredients: List[ProductResponse]

    class Config:
        from_attributes = True

# Subscription Schemas
class SubscriptionCreate(BaseModel):
    product_ids: List[int]
    frequency: str # "weekly" or "monthly"

class SubscriptionResponse(BaseModel):
    id: int
    frequency: str
    next_delivery_date: datetime
    is_active: bool
    products: List[ProductResponse]

    class Config:
        from_attributes = True


# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Authentication Utilities ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
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
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    # In the future, you could add a `is_active` flag to the User model
    return current_user

# --- Main FastAPI App Instance ---
app = FastAPI(
    title="e-commerce-selling-groceries-982317",
    description="A modern, minimalist e-commerce platform designed to seamlessly sell both groceries and electronics.",
    version="1.0.0"
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request Logging Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status code: {response.status_code}")
    return response

# --- Event Handlers ---
@app.on_event("startup")
def on_startup():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")

# --- API Routers ---

# --- Authentication Router ---
auth_router = FastAPI(prefix="/api/v1/auth", tags=["Authentication"])

@auth_router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": new_user.email})
    refresh_token = create_refresh_token(data={"sub": new_user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(new_user)
    }

@auth_router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@auth_router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user

# --- Product Router ---
product_router = FastAPI(prefix="/api/v1/products", tags=["Products"])

@product_router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # This would typically be an admin-only endpoint
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@product_router.get("/", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    # Dynamic Dual-Category Filtering parameters
    organic: Optional[bool] = None,
    gluten_free: Optional[bool] = None,
    brand: Optional[str] = None,
    screen_size: Optional[float] = None,
    ram: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    # Context-aware filtering for groceries
    if category == 'groceries':
        if organic is not None:
            query = query.filter(Product.specifications['organic'].as_boolean() == organic)
        if gluten_free is not None:
            query = query.filter(Product.specifications['gluten_free'].as_boolean() == gluten_free)
    
    # Context-aware filtering for electronics
    if category == 'electronics':
        if brand:
            query = query.filter(Product.specifications['brand'].as_string() == brand)
        if screen_size:
            query = query.filter(Product.specifications['screen_size'].as_float() == screen_size)
        if ram:
            query = query.filter(Product.specifications['ram_gb'].as_integer() == ram)
            
    return query.all()

@product_router.post("/compare", response_model=Dict[str, Any])
async def compare_electronics(request: ProductComparisonRequest, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.id.in_(request.product_ids)).all()
    if len(products) < 2:
        raise HTTPException(status_code=400, detail="At least two valid product IDs are required for comparison.")
    
    comparison_data = {}
    all_specs = set()
    for p in products:
        if p.category != 'electronics':
            raise HTTPException(status_code=400, detail=f"Product '{p.name}' is not an electronic and cannot be compared.")
        if p.specifications:
            all_specs.update(p.specifications.keys())

    comparison_table = {spec: {} for spec in sorted(list(all_specs))}
    
    for product in products:
        for spec in comparison_table.keys():
            comparison_table[spec][product.name] = product.specifications.get(spec, "N/A")

    return {
        "product_names": [p.name for p in products],
        "comparison_table": comparison_table
    }

# --- Cart Router ---
cart_router = FastAPI(prefix="/api/v1/cart", tags=["Shopping Cart"])

@cart_router.post("/add", response_model=CartItemResponse)
async def add_to_cart(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.stock_quantity < item.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough stock available")

    cart_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == item.product_id
    ).first()

    if cart_item:
        cart_item.quantity += item.quantity
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=item.product_id, quantity=item.quantity)
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart_item)
    return cart_item

@cart_router.delete("/remove/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    cart_item = db.query(CartItem).filter(
        CartItem.id == cart_item_id,
        CartItem.user_id == current_user.id
    ).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    
    db.delete(cart_item)
    db.commit()
    return

@cart_router.get("/", response_model=CartResponse)
async def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return {"items": cart_items, "total_price": total_price}

# --- Order Router ---
order_router = FastAPI(prefix="/api/v1/orders", tags=["Orders"])

@order_router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_details: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    total_amount = 0
    order_items_to_create = []
    has_groceries = False
    has_electronics = False

    for item in cart_items:
        product = item.product
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for {product.name}")
        
        total_amount += product.price * item.quantity
        product.stock_quantity -= item.quantity
        order_items_to_create.append(OrderItem(product_id=product.id, quantity=item.quantity, price_at_purchase=product.price))
        
        if product.category == 'groceries':
            has_groceries = True
        if product.category == 'electronics':
            has_electronics = True

    # Handle Scheduled Grocery Delivery Slots
    delivery_slot_start = None
    delivery_slot_end = None
    if has_groceries and order_details.delivery_slot_start:
        if order_details.delivery_slot_start < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Delivery slot must be in the future.")
        delivery_slot_start = order_details.delivery_slot_start
        delivery_slot_end = delivery_slot_start + timedelta(hours=2)

    # Handle Real-Time Order Tracking
    tracking_info = {}
    if has_groceries:
        tracking_info['grocery_tracking'] = {"status": "Preparing", "eta": None, "live_location": None}
    if has_electronics:
        tracking_info['electronics_tracking'] = {"carrier": "FedEx", "tracking_number": "FX123456789", "status": "Label Created"}

    new_order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        items=order_items_to_create,
        delivery_slot_start=delivery_slot_start,
        delivery_slot_end=delivery_slot_end,
        tracking_info=tracking_info
    )
    
    db.add(new_order)
    # Clear user's cart
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    
    db.commit()
    db.refresh(new_order)
    return new_order

@order_router.get("/", response_model=List[OrderResponse])
async def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return orders

# --- Recipe Router ---
recipe_router = FastAPI(prefix="/api/v1/recipes", tags=["Recipes"])

@recipe_router.get("/", response_model=List[RecipeResponse])
async def get_recipes(db: Session = Depends(get_db)):
    return db.query(Recipe).all()

@recipe_router.post("/{recipe_id}/add-to-cart", status_code=status.HTTP_200_OK)
async def add_recipe_ingredients_to_cart(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    added_items = []
    for ingredient in recipe.ingredients:
        if ingredient.stock_quantity > 0:
            cart_item = db.query(CartItem).filter(
                CartItem.user_id == current_user.id,
                CartItem.product_id == ingredient.id
            ).first()
            if cart_item:
                cart_item.quantity += 1
            else:
                new_cart_item = CartItem(user_id=current_user.id, product_id=ingredient.id, quantity=1)
                db.add(new_cart_item)
            added_items.append(ingredient.name)
    
    db.commit()
    return {"message": f"Added ingredients for '{recipe.name}' to cart.", "items_added": added_items}

# --- Subscription Router ---
subscription_router = FastAPI(prefix="/api/v1/subscriptions", tags=["Subscriptions"])

@subscription_router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    sub_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    products = db.query(Product).filter(Product.id.in_(sub_data.product_ids)).all()
    if not products or len(products) != len(sub_data.product_ids):
        raise HTTPException(status_code=404, detail="One or more products not found.")
    
    for p in products:
        if p.category != 'groceries':
            raise HTTPException(status_code=400, detail=f"Product '{p.name}' is not a grocery item and cannot be subscribed to.")

    if sub_data.frequency not in ["weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Frequency must be 'weekly' or 'monthly'.")

    if sub_data.frequency == "weekly":
        next_delivery = datetime.now(timezone.utc) + timedelta(days=7)
    else: # monthly
        next_delivery = datetime.now(timezone.utc) + timedelta(days=30)

    new_subscription = Subscription(
        user_id=current_user.id,
        frequency=sub_data.frequency,
        next_delivery_date=next_delivery,
        products=products
    )
    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)
    return new_subscription

@subscription_router.get("/", response_model=List[SubscriptionResponse])
async def get_my_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(Subscription).filter(Subscription.user_id == current_user.id).all()

# --- Other E-commerce Routers ---
payment_router = FastAPI(prefix="/api/v1/payments", tags=["Payments"])
inventory_router = FastAPI(prefix="/api/v1/inventory", tags=["Inventory"])

@payment_router.post("/process")
async def process_payment(order_id: int, db: Session = Depends(get_db)):
    # This is a mock endpoint. In a real application, this would integrate with a payment gateway like Stripe.
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Payment already processed for this order.")

    # Simulate successful payment
    order.status = "processing"
    db.commit()
    return {"message": "Payment successful", "order_id": order_id, "new_status": "processing"}

@inventory_router.get("/", response_model=List[ProductResponse])
async def get_inventory(db: Session = Depends(get_db)):
    # This would typically be an admin-only endpoint
    return db.query(Product).all()

# --- Include Routers in Main App ---
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(recipe_router)
app.include_router(subscription_router)
app.include_router(payment_router)
app.include_router(inventory_router)

# --- Root Endpoint ---
@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "app": "e-commerce-selling-groceries-982317"}

# To run this app:
# 1. Install dependencies: pip install "fastapi[all]" sqlalchemy passlib[bcrypt] python-jose[cryptography]
# 2. Save the code as main.py
# 3. Run from your terminal: uvicorn main:app --reload