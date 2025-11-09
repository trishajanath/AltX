# models_fixed.py - Comprehensive models file with both Pydantic and SQLAlchemy models

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean, JSON, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# --- Database Configuration ---
DATABASE_URL = "sqlite:///./ecommerce_groceries.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Enums ---
class ProductCategory(str, Enum):
    """Enum for product categories."""
    GROCERY = "Grocery"
    ELECTRONICS = "Electronics"

class OrderStatus(str, Enum):
    """Enum for order statuses."""
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"

# --- SQLAlchemy Database Models ---

class UserDB(Base):
    """SQLAlchemy User model for database"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = relationship("OrderDB", back_populates="user")
    cart_items = relationship("CartItemDB", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

class ProductDB(Base):
    """SQLAlchemy Product model for database"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    category = Column(String, nullable=False)
    image_urls = Column(JSON, default=list)
    attributes = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cart_items = relationship("CartItemDB", back_populates="product")
    order_items = relationship("OrderItemDB", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}')>"

class CartItemDB(Base):
    """SQLAlchemy Cart Item model for database"""
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserDB", back_populates="cart_items")
    product = relationship("ProductDB", back_populates="cart_items")
    
    def __repr__(self):
        return f"<CartItem(id={self.id}, user_id={self.user_id}, product_id={self.product_id}, qty={self.quantity})>"

class OrderDB(Base):
    """SQLAlchemy Order model for database"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default=OrderStatus.PENDING.value)
    total_amount = Column(Float, nullable=False)
    shipping_address = Column(JSON, nullable=True)
    payment_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserDB", back_populates="orders")
    order_items = relationship("OrderItemDB", back_populates="order")
    
    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, status='{self.status}', total=${self.total_amount})>"

class OrderItemDB(Base):
    """SQLAlchemy Order Item model for database"""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("OrderDB", back_populates="order_items")
    product = relationship("ProductDB", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>"

# --- Pydantic API Models ---

# User Models
class UserBase(BaseModel):
    """Base Pydantic model for User"""
    model_config = ConfigDict(from_attributes=True)
    
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    """Pydantic model for creating a user"""
    password: str

class UserUpdate(BaseModel):
    """Pydantic model for updating a user"""
    model_config = ConfigDict(from_attributes=True)
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    """Pydantic model for user API responses"""
    id: int
    created_at: datetime
    updated_at: datetime

# Product Models
class ProductBase(BaseModel):
    """Base Pydantic model for Product"""
    model_config = ConfigDict(from_attributes=True)
    
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int = 0
    category: ProductCategory
    image_urls: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

class ProductCreate(ProductBase):
    """Pydantic model for creating a product"""
    pass

class ProductUpdate(BaseModel):
    """Pydantic model for updating a product"""
    model_config = ConfigDict(from_attributes=True)
    
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    category: Optional[ProductCategory] = None
    image_urls: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    """Pydantic model for product API responses"""
    id: int
    created_at: datetime
    updated_at: datetime

# Cart Models
class CartItemBase(BaseModel):
    """Base Pydantic model for Cart Item"""
    model_config = ConfigDict(from_attributes=True)
    
    product_id: int
    quantity: int = 1

class CartItemCreate(CartItemBase):
    """Pydantic model for creating a cart item"""
    pass

class CartItemUpdate(BaseModel):
    """Pydantic model for updating a cart item"""
    model_config = ConfigDict(from_attributes=True)
    
    quantity: Optional[int] = None

class CartItemResponse(CartItemBase):
    """Pydantic model for cart item API responses"""
    id: int
    user_id: int
    product: ProductResponse
    created_at: datetime
    updated_at: datetime

# Order Models
class OrderBase(BaseModel):
    """Base Pydantic model for Order"""
    model_config = ConfigDict(from_attributes=True)
    
    shipping_address: Optional[Dict[str, Any]] = None
    payment_info: Optional[Dict[str, Any]] = None

class OrderCreate(OrderBase):
    """Pydantic model for creating an order"""
    pass

class OrderUpdate(BaseModel):
    """Pydantic model for updating an order"""
    model_config = ConfigDict(from_attributes=True)
    
    status: Optional[OrderStatus] = None
    shipping_address: Optional[Dict[str, Any]] = None
    payment_info: Optional[Dict[str, Any]] = None

class OrderResponse(OrderBase):
    """Pydantic model for order API responses"""
    id: int
    user_id: int
    status: OrderStatus
    total_amount: float
    order_items: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

# Authentication Models
class Token(BaseModel):
    """JWT Token response model"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Token data for JWT processing"""
    email: Optional[str] = None

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str