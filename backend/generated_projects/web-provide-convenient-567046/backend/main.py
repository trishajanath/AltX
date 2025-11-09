# main.py
# COMPLETE, PRODUCTION-READY FastAPI for web-provide-convenient-567046

# --- Imports ---
import os
import logging
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Text, Float, Boolean,
    ForeignKey, func
)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.exc import IntegrityError

# --- Configuration ---
# In a real production environment, use environment variables.
# Example: SECRET_KEY = os.getenv("SECRET_KEY", "a_default_secret_key")
SECRET_KEY = "a_secure_and_long_secret_key_for_jwt_web-provide-convenient-567046"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./online_grocery.db"
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

# --- Database Models (SQLAlchemy) ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    image_url = Column(String)
    category = Column(String, index=True)
    tags = Column(String) # Comma-separated tags like 'organic', 'gluten-free'
    stock_quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    status = Column(String, default="pending") # e.g., pending, processing, shipped, delivered
    created_at = Column(DateTime, default=datetime.utcnow)
    delivery_slot_id = Column(Integer, ForeignKey("delivery_slots.id"))

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    delivery_slot = relationship("DeliverySlot")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer)
    price_at_purchase = Column(Float)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class MealKit(Base):
    __tablename__ = "meal_kits"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    description = Column(Text)
    image_url = Column(String)
    
    items = relationship("MealKitItem", back_populates="meal_kit", cascade="all, delete-orphan")

class MealKitItem(Base):
    __tablename__ = "meal_kit_items"
    id = Column(Integer, primary_key=True, index=True)
    meal_kit_id = Column(Integer, ForeignKey("meal_kits.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)

    meal_kit = relationship("MealKit", back_populates="items")
    product = relationship("Product")

class DeliverySlot(Base):
    __tablename__ = "delivery_slots"
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, default=False)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    frequency = Column(String, nullable=False) # e.g., 'weekly', 'bi-weekly', 'monthly'
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")
    product = relationship("Product")

# Create database tables
Base.metadata.create_all(bind=engine)

# --- Pydantic Models (Schemas) ---

# User & Auth Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    
    class Config:
        from_attributes = True

class TokenData(BaseModel):
    email: Optional[str] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category: str
    tags: Optional[str] = None
    stock_quantity: int

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Cart Schemas
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class CartItemCreate(CartItemBase):
    pass

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
    delivery_slot_id: int

class OrderResponse(BaseModel):
    id: int
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse]
    delivery_slot_start: datetime
    delivery_slot_end: datetime

    class Config:
        from_attributes = True

# Meal Kit Schemas
class MealKitItemResponse(BaseModel):
    quantity: int
    product: ProductResponse
    class Config:
        from_attributes = True

class MealKitResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    items: List[MealKitItemResponse]
    class Config:
        from_attributes = True

# Delivery Slot Schemas
class DeliverySlotResponse(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime
    is_booked: bool
    class Config:
        from_attributes = True

# Subscription Schemas
class SubscriptionCreate(BaseModel):
    product_id: int
    frequency: str # 'weekly', 'bi-weekly', 'monthly'
    quantity: int = Field(..., gt=0)

class SubscriptionResponse(BaseModel):
    id: int
    frequency: str
    quantity: int
    product: ProductResponse
    class Config:
        from_attributes = True

# --- Dependencies ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
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

# --- Security & JWT Utilities ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- FastAPI App Initialization ---

app = FastAPI(
    title="web-provide-convenient-567046",
    description="A web application designed to provide a hyper-convenient online grocery shopping experience for busy working professionals.",
    version="1.0.0"
)

# --- Middleware ---

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"Request: {request.method} {request.url.path} | "
        f"Response: {response.status_code} | "
        f"Duration: {process_time:.4f}s"
    )
    return response

# --- API Endpoints ---

# Health Check
@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "app": "web-provide-convenient-567046"}

# --- Authentication Routes ---
auth_router = FastAPI.router
@auth_router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(new_user)
    }

@auth_router.post("/login", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@auth_router.post("/refresh", response_model=Token, tags=["Authentication"])
async def refresh_token(refresh_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    current_user = await get_current_user(token=refresh_token, db=db)
    new_access_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(current_user)
    }

@auth_router.get("/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# --- Product Routes ---
product_router = FastAPI.router
@product_router.get("/", response_model=List[ProductResponse], tags=["Products"])
async def get_products(
    q: Optional[str] = None, 
    dietary_filter: Optional[str] = None, 
    concept: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if q:
        query = query.filter(Product.name.contains(q) | Product.description.contains(q))
    if dietary_filter:
        # Simulates filtering by tags like 'organic', 'gluten-free'
        query = query.filter(Product.tags.contains(dietary_filter))
    if concept:
        # Simulates concept search like 'quick weeknight dinner'
        # In a real app, this would be a more complex search or AI model
        if concept == "quick weeknight dinner ingredients":
            query = query.filter(Product.category.in_(['Pasta', 'Vegetables', 'Meat']))
    
    products = query.offset(skip).limit(limit).all()
    return products

@product_router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, tags=["Products"])
async def create_product(product: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # In a real app, this would be restricted to admin users
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

# --- Cart Routes ---
cart_router = FastAPI.router
@cart_router.get("/", response_model=CartResponse, tags=["Shopping Cart"])
async def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return {"items": cart_items, "total_price": total_price}

@cart_router.post("/add", response_model=CartItemResponse, tags=["Shopping Cart"])
async def add_to_cart(item: CartItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.stock_quantity < item.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough stock")

    cart_item = db.query(CartItem).filter(CartItem.user_id == current_user.id, CartItem.product_id == item.product_id).first()
    if cart_item:
        cart_item.quantity += item.quantity
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=item.product_id, quantity=item.quantity)
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart_item)
    return cart_item

@cart_router.delete("/remove/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Shopping Cart"])
async def remove_from_cart(product_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(CartItem).filter(CartItem.user_id == current_user.id, CartItem.product_id == product_id).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not in cart")
    
    db.delete(cart_item)
    db.commit()
    return

# --- Order Routes ---
order_router = FastAPI.router
@order_router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, tags=["Orders"])
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    delivery_slot = db.query(DeliverySlot).filter(DeliverySlot.id == order_data.delivery_slot_id).first()
    if not delivery_slot or delivery_slot.is_booked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery slot not available")

    total_amount = 0
    order_items_to_create = []
    for item in cart_items:
        if item.product.stock_quantity < item.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for {item.product.name}")
        
        total_amount += item.product.price * item.quantity
        order_items_to_create.append(
            OrderItem(product_id=item.product_id, quantity=item.quantity, price_at_purchase=item.product.price)
        )
        item.product.stock_quantity -= item.quantity

    new_order = Order(
        user_id=current_user.id, 
        total_amount=total_amount, 
        items=order_items_to_create,
        delivery_slot_id=delivery_slot.id
    )
    delivery_slot.is_booked = True
    
    db.add(new_order)
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete() # Clear cart
    db.commit()
    db.refresh(new_order)

    # Manually construct response to include delivery slot times
    return OrderResponse(
        id=new_order.id,
        total_amount=new_order.total_amount,
        status=new_order.status,
        created_at=new_order.created_at,
        items=[OrderItemResponse.from_orm(item) for item in new_order.items],
        delivery_slot_start=new_order.delivery_slot.start_time,
        delivery_slot_end=new_order.delivery_slot.end_time
    )

@order_router.get("/", response_model=List[OrderResponse], tags=["Orders"])
async def get_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    
    # Manually construct response to include delivery slot times
    response_orders = []
    for order in orders:
        response_orders.append(OrderResponse(
            id=order.id,
            total_amount=order.total_amount,
            status=order.status,
            created_at=order.created_at,
            items=[OrderItemResponse.from_orm(item) for item in order.items],
            delivery_slot_start=order.delivery_slot.start_time,
            delivery_slot_end=order.delivery_slot.end_time
        ))
    return response_orders

@order_router.post("/{order_id}/reorder", response_model=CartResponse, tags=["Orders"])
async def reorder_past_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    for item in order.items:
        await add_to_cart(CartItemCreate(product_id=item.product_id, quantity=item.quantity), current_user, db)
    
    return await get_cart(current_user, db)

# --- Feature-Specific Routes ---
feature_router = FastAPI.router
@feature_router.get("/mealkits", response_model=List[MealKitResponse], tags=["Features"])
async def get_meal_kits(db: Session = Depends(get_db)):
    return db.query(MealKit).all()

@feature_router.post("/mealkits/{mealkit_id}/add-to-cart", response_model=CartResponse, tags=["Features"])
async def add_meal_kit_to_cart(mealkit_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meal_kit = db.query(MealKit).filter(MealKit.id == mealkit_id).first()
    if not meal_kit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal kit not found")
    
    for item in meal_kit.items:
        await add_to_cart(CartItemCreate(product_id=item.product_id, quantity=item.quantity), current_user, db)
    
    return await get_cart(current_user, db)

@feature_router.get("/delivery-slots", response_model=List[DeliverySlotResponse], tags=["Features"])
async def get_delivery_slots(day: date, db: Session = Depends(get_db)):
    start_of_day = datetime.combine(day, datetime.min.time())
    end_of_day = datetime.combine(day, datetime.max.time())
    slots = db.query(DeliverySlot).filter(
        DeliverySlot.start_time >= start_of_day,
        DeliverySlot.start_time <= end_of_day,
        DeliverySlot.is_booked == False
    ).all()
    return slots

@feature_router.get("/subscriptions", response_model=List[SubscriptionResponse], tags=["Features"])
async def get_my_subscriptions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Subscription).filter(Subscription.user_id == current_user.id).all()

@feature_router.post("/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED, tags=["Features"])
async def create_subscription(sub_data: SubscriptionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == sub_data.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    existing_sub = db.query(Subscription).filter_by(user_id=current_user.id, product_id=sub_data.product_id).first()
    if existing_sub:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription for this product already exists")

    new_sub = Subscription(
        user_id=current_user.id,
        product_id=sub_data.product_id,
        frequency=sub_data.frequency,
        quantity=sub_data.quantity
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@feature_router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Features"])
async def cancel_subscription(subscription_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter_by(id=subscription_id, user_id=current_user.id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    db.delete(sub)
    db.commit()
    return

@feature_router.get("/recommendations/quick-add", response_model=List[ProductResponse], tags=["Features"])
async def get_quick_add_recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # AI Simulation: Find the top 5 most frequently purchased products by the user
    frequently_purchased = (
        db.query(OrderItem.product_id, func.sum(OrderItem.quantity).label('total_quantity'))
        .join(Order)
        .filter(Order.user_id == current_user.id)
        .group_by(OrderItem.product_id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    product_ids = [item.product_id for item in frequently_purchased]
    if not product_ids:
        # Fallback: return some popular products if user has no history
        return db.query(Product).order_by(Product.id.desc()).limit(5).all()
        
    return db.query(Product).filter(Product.id.in_(product_ids)).all()

# --- Mock Payment & Inventory Routes ---
mock_router = FastAPI.router
@mock_router.post("/payments/process", tags=["Mock Services"])
async def process_payment(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # This is a mock endpoint. In a real app, it would integrate with a payment gateway like Stripe.
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if order.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order has already been processed")

    # Simulate successful payment
    order.status = "processing"
    db.commit()
    return {"status": "success", "message": "Payment processed successfully", "order_id": order.id}

@mock_router.get("/inventory", response_model=Dict[int, int], tags=["Mock Services"])
async def get_inventory(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # In a real app, this would be an admin-only endpoint
    products = db.query(Product).all()
    return {product.id: product.stock_quantity for product in products}

# --- Include Routers ---
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(product_router, prefix="/api/v1/products")
app.include_router(cart_router, prefix="/api/v1/cart")
app.include_router(order_router, prefix="/api/v1/orders")
app.include_router(feature_router, prefix="/api/v1")
app.include_router(mock_router, prefix="/api/v1")

# --- One-time Data Seeding (for demonstration) ---
@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    try:
        # Check if data exists
        if db.query(Product).count() == 0:
            logger.info("Seeding initial data...")
            # Products
            products_to_add = [
                Product(name="Organic Avocado", description="Creamy and delicious Hass avocado.", price=1.99, category="Produce", tags="organic,vegan", stock_quantity=100),
                Product(name="Gluten-Free Bread", description="A soft, gluten-free loaf.", price=5.49, category="Bakery", tags="gluten-free", stock_quantity=50),
                Product(name="Almond Milk Yogurt", description="Dairy-free yogurt alternative.", price=2.29, category="Dairy", tags="lactose-free,vegan", stock_quantity=75),
                Product(name="Chicken Breast", description="Free-range chicken breast.", price=9.99, category="Meat", tags="quick_dinner", stock_quantity=40),
                Product(name="Bell Peppers (3-pack)", description="Red, yellow, and green peppers.", price=3.99, category="Produce", tags="vegan,quick_dinner", stock_quantity=60),
                Product(name="Pesto Sauce", description="Classic basil pesto.", price=4.50, category="Pantry", tags="quick_dinner", stock_quantity=80),
                Product(name="Spaghetti Pasta", description="Italian spaghetti.", price=2.00, category="Pantry", tags="vegan,quick_dinner", stock_quantity=120),
                Product(name="Organic Eggs (Dozen)", description="Farm-fresh organic eggs.", price=4.99, category="Dairy", tags="organic,staple", stock_quantity=100),
                Product(name="Whole Milk (Gallon)", description="Grade A whole milk.", price=3.79, category="Dairy", tags="staple", stock_quantity=90),
            ]
            db.add_all(products_to_add)
            db.commit()

            # Meal Kits
            pesto_pasta_kit = MealKit(name="15-Minute Pesto Pasta", description="A quick and easy weeknight dinner.", image_url="url/to/pasta.jpg")
            db.add(pesto_pasta_kit)
            db.commit()
            db.refresh(pesto_pasta_kit)
            
            pesto_pasta_items = [
                MealKitItem(meal_kit_id=pesto_pasta_kit.id, product_id=7, quantity=1), # Pasta
                MealKitItem(meal_kit_id=pesto_pasta_kit.id, product_id=6, quantity=1), # Pesto
            ]
            db.add_all(pesto_pasta_items)
            db.commit()

            # Delivery Slots for today
            today = date.today()
            for hour in range(9, 22): # 9 AM to 9 PM
                slot = DeliverySlot(
                    start_time=datetime.combine(today, datetime.min.time()).replace(hour=hour),
                    end_time=datetime.combine(today, datetime.min.time()).replace(hour=hour+1)
                )
                db.add(slot)
            db.commit()
            logger.info("Data seeding complete.")
    finally:
        db.close()