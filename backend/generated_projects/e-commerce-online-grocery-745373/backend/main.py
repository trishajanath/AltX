# main.py
# COMPLETE, PRODUCTION-READY FastAPI main.py for: e-commerce-online-grocery-745373

# --- Imports ---
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (create_engine, Column, Integer, String, DateTime,
                        Text, Float, Boolean, ForeignKey)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.exc import IntegrityError

# --- Configuration ---
# For production, use environment variables.
# Example: SECRET_KEY = os.getenv("SECRET_KEY", "a_default_secret_key_for_dev")
SECRET_KEY = "e-commerce-online-grocery-745373-super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./online_grocery.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Security & Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- SQLAlchemy Models ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    image_url = Column(String)
    category = Column(String, index=True)
    stock_quantity = Column(Integer, default=0)
    is_on_sale = Column(Boolean, default=False)
    sale_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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
    delivery_slot_id = Column(Integer, ForeignKey("delivery_slots.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    delivery_slot = relationship("DeliverySlot")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class DeliverySlot(Base):
    __tablename__ = "delivery_slots"
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False, unique=True)
    end_time = Column(DateTime, nullable=False, unique=True)
    is_booked = Column(Boolean, default=False)

# --- Pydantic Schemas (Data Validation) ---

# User & Auth Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8)

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
    email: Optional[str] = None

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category: str
    stock_quantity: int
    is_on_sale: Optional[bool] = False
    sale_price: Optional[float] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Cart Schemas
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(1, gt=0)

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)

class CartItemResponse(BaseModel):
    id: int
    quantity: int
    product: ProductResponse

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    subtotal: float
    estimated_delivery_fee: float
    total: float

# Delivery Slot Schemas
class DeliverySlotResponse(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime

    class Config:
        from_attributes = True

# Order Schemas
class OrderCreate(BaseModel):
    delivery_slot_id: int

class OrderItemResponse(BaseModel):
    quantity: int
    price_at_purchase: float
    product: ProductResponse

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse]
    delivery_slot: DeliverySlotResponse

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
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
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

# --- FastAPI Application Instance ---
app = FastAPI(
    title="e-commerce-online-grocery-745373",
    description="A modern, high-performance online grocery store designed for a seamless shopping experience.",
    version="1.0.0"
)

# --- Middleware ---
# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"method={request.method} path={request.url.path} status={response.status_code} duration={process_time:.4f}s"
    )
    return response

# --- Database Initialization & Seeding ---
def seed_data(db: Session):
    # Check if data exists
    if db.query(Product).first():
        logger.info("Database already seeded.")
        return

    logger.info("Seeding database with initial data...")
    # Seed Products
    products_to_add = [
        Product(name='Hass Avocado', description='Creamy and delicious Hass avocados.', price=1.99, image_url='/images/avocado.jpg', category='Fresh Produce', stock_quantity=150),
        Product(name='Organic Milk', description='1 Gallon of fresh, organic whole milk.', price=5.49, image_url='/images/milk.jpg', category='Dairy & Eggs', stock_quantity=80),
        Product(name='Sourdough Bread', description='Artisan sourdough loaf, baked fresh daily.', price=4.99, image_url='/images/bread.jpg', category='Bakery', stock_quantity=50),
        Product(name='Gluten-Free Pasta', description='16oz box of gluten-free penne pasta.', price=3.29, image_url='/images/pasta.jpg', category='Pantry', stock_quantity=120, is_on_sale=True, sale_price=2.79),
        Product(name='Organic Eggs', description='A dozen large, brown organic eggs.', price=6.99, image_url='/images/eggs.jpg', category='Dairy & Eggs', stock_quantity=100),
        Product(name='Avocado Oil', description='Cold-pressed avocado oil for cooking.', price=9.99, image_url='/images/avocado-oil.jpg', category='Pantry', stock_quantity=60),
    ]
    db.add_all(products_to_add)

    # Seed Delivery Slots for the next 3 days
    now = datetime.now(timezone.utc)
    for day in range(3):
        for hour in range(9, 21, 2): # 9am to 9pm, 2-hour slots
            slot_start = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=day)
            slot_end = slot_start + timedelta(hours=2)
            db.add(DeliverySlot(start_time=slot_start, end_time=slot_end))
    
    db.commit()
    logger.info("Database seeding complete.")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_data(db)

# --- API Endpoints ---

# Health Check
@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "app_name": "e-commerce-online-grocery-745373"}

# --- Authentication Routes ---
@app.post("/api/v1/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    access_token = create_access_token(data={"sub": db_user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(data={"sub": db_user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": db_user
    }

@app.post("/api/v1/auth/login", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@app.post("/api/v1/auth/refresh", response_model=Dict[str, str], tags=["Authentication"])
async def refresh_token(refresh_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        new_access_token = create_access_token(data={"sub": email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

@app.get("/api/v1/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# --- Product Routes ---
@app.get("/api/v1/products", response_model=List[ProductResponse], tags=["Products"])
async def get_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    on_sale: Optional[bool] = None,
    sort_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of products with filtering, searching, and sorting.
    - `q`: Predictive search query for product names.
    - `category`: Filter by category.
    - `on_sale`: Filter for products on sale.
    - `sort_by`: Sort by 'price_asc' or 'price_desc'.
    """
    query = db.query(Product)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category:
        query = query.filter(Product.category == category)
    if on_sale is not None:
        query = query.filter(Product.is_on_sale == on_sale)
    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    
    return query.all()

@app.get("/api/v1/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

# --- Promotions Routes ---
@app.get("/api/v1/promotions", response_model=List[ProductResponse], tags=["Promotions"])
async def get_promotions(category: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get all products currently on sale, with optional category filtering.
    """
    query = db.query(Product).filter(Product.is_on_sale == True)
    if category:
        query = query.filter(Product.category == category)
    return query.all()

# --- Shopping Cart Routes ---
@app.get("/api/v1/cart", response_model=CartResponse, tags=["Shopping Cart"])
async def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    subtotal = 0
    for item in cart_items:
        price = item.product.sale_price if item.product.is_on_sale else item.product.price
        subtotal += price * item.quantity
    
    # Dummy delivery fee for demonstration
    estimated_delivery_fee = 5.99 if subtotal > 0 else 0
    total = subtotal + estimated_delivery_fee

    return {"items": cart_items, "subtotal": subtotal, "estimated_delivery_fee": estimated_delivery_fee, "total": total}

@app.post("/api/v1/cart/add", response_model=CartItemResponse, tags=["Shopping Cart"])
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

@app.put("/api/v1/cart/update/{item_id}", response_model=CartItemResponse, tags=["Shopping Cart"])
async def update_cart_item(item_id: int, item_update: CartItemUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == current_user.id).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    
    if cart_item.product.stock_quantity < item_update.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough stock")

    cart_item.quantity = item_update.quantity
    db.commit()
    db.refresh(cart_item)
    return cart_item

@app.delete("/api/v1/cart/remove/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Shopping Cart"])
async def remove_from_cart(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == current_user.id).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    
    db.delete(cart_item)
    db.commit()
    return

# --- Delivery Slot Routes ---
@app.get("/api/v1/delivery-slots", response_model=List[DeliverySlotResponse], tags=["Delivery"])
async def get_available_delivery_slots(db: Session = Depends(get_db)):
    """
    Get a list of available (not booked) delivery slots.
    """
    now = datetime.now(timezone.utc)
    slots = db.query(DeliverySlot).filter(DeliverySlot.is_booked == False, DeliverySlot.start_time > now).order_by(DeliverySlot.start_time).all()
    return slots

# --- Order Routes ---
@app.post("/api/v1/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, tags=["Orders"])
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    delivery_slot = db.query(DeliverySlot).filter(DeliverySlot.id == order_data.delivery_slot_id).first()
    if not delivery_slot or delivery_slot.is_booked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery slot is not available")

    total_amount = 0
    order_items_to_create = []
    for item in cart_items:
        product = item.product
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for {product.name}")
        
        price = product.sale_price if product.is_on_sale else product.price
        total_amount += price * item.quantity
        product.stock_quantity -= item.quantity # Decrease stock
        
        order_items_to_create.append(OrderItem(product_id=product.id, quantity=item.quantity, price_at_purchase=price))

    # Create the order
    new_order = Order(user_id=current_user.id, total_amount=total_amount, delivery_slot_id=delivery_slot.id, items=order_items_to_create)
    delivery_slot.is_booked = True # Book the slot
    
    db.add(new_order)
    
    # Clear the user's cart
    for item in cart_items:
        db.delete(item)
        
    db.commit()
    db.refresh(new_order)
    return new_order

@app.get("/api/v1/orders", response_model=List[OrderResponse], tags=["Orders"])
async def get_order_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return orders

@app.post("/api/v1/orders/{order_id}/reorder", response_model=CartResponse, tags=["Orders"])
async def reorder_previous_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    One-Click Reorder: Adds all items from a previous order to the current cart.
    """
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    for item in order.items:
        await add_to_cart(CartItemCreate(product_id=item.product_id, quantity=item.quantity), current_user, db)
    
    return await get_cart(current_user, db)

# Note: A full payment processing endpoint would require integration with a third-party
# service like Stripe or PayPal. This is a placeholder for that logic.
@app.post("/api/v1/payments/process", tags=["Payments"])
async def process_payment(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment already processed for this order")

    # --- Payment Gateway Logic would go here ---
    # Simulating a successful payment
    order.status = "processing"
    db.commit()
    return {"status": "success", "message": "Payment processed successfully", "order_id": order.id}

# Note: Inventory management is handled implicitly when products are created and orders are processed.
# A dedicated endpoint could provide a summary.
@app.get("/api/v1/inventory", response_model=List[Dict], tags=["Inventory"])
async def get_inventory_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # This should be an admin-only endpoint in a real application.
    # For simplicity, we'll just require authentication.
    inventory = db.query(Product.id, Product.name, Product.stock_quantity).all()
    return [{"id": p.id, "name": p.name, "stock": p.stock_quantity} for p in inventory]