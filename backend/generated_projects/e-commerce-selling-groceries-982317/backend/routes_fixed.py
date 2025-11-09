# routes_fixed.py - Modular FastAPI routes that import from models.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

# Import ALL models from models.py (DO NOT recreate them)
from models_fixed import *

router = APIRouter()

# --- Dependencies ---
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- User Authentication Routes ---

@router.post("/auth/register", response_model=UserResponse, tags=["Authentication"])
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password (you would import this from main.py or create a utils module)
    # For now, storing plain text (NOT SECURE - just for example)
    hashed_password = user.password + "_hashed"  # Placeholder
    
    # Create new user using SQLAlchemy model from models.py
    db_user = UserDB(
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name,
        is_active=user.is_active
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    # Find user using SQLAlchemy model from models.py
    user = db.query(UserDB).filter(UserDB.email == login_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password (placeholder logic)
    if user.password_hash != login_data.password + "_hashed":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token (you would import this from main.py)
    access_token = f"fake_token_for_{user.email}"  # Placeholder
    
    return {"access_token": access_token, "token_type": "bearer"}

# --- Product Routes ---

@router.get("/products", response_model=List[ProductResponse], tags=["Products"])
async def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all products using SQLAlchemy model from models.py"""
    products = db.query(ProductDB).filter(ProductDB.is_active == True).offset(skip).limit(limit).all()
    return products

@router.post("/products", response_model=ProductResponse, tags=["Products"])
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product using SQLAlchemy model from models.py"""
    # Check if SKU already exists
    existing_product = db.query(ProductDB).filter(ProductDB.sku == product.sku).first()
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{product.sku}' already exists"
        )
    
    # Create new product using SQLAlchemy model from models.py
    db_product = ProductDB(
        sku=product.sku,
        name=product.name,
        description=product.description,
        price=product.price,
        stock_quantity=product.stock_quantity,
        category=product.category.value,
        image_urls=product.image_urls,
        attributes=product.attributes,
        is_active=product.is_active
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product

@router.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID using SQLAlchemy model from models.py"""
    product = db.query(ProductDB).filter(ProductDB.id == product_id, ProductDB.is_active == True).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    return product

@router.put("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def update_product(product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db)):
    """Update a product using SQLAlchemy model from models.py"""
    db_product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Update only provided fields
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "category" and value:
            setattr(db_product, field, value.value)
        else:
            setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    
    return db_product

@router.delete("/products/{product_id}", tags=["Products"])
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Soft delete a product using SQLAlchemy model from models.py"""
    db_product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Soft delete by setting is_active to False
    db_product.is_active = False
    db.commit()
    
    return {"message": f"Product with ID {product_id} deleted successfully"}

# --- Cart Routes ---

@router.get("/cart", response_model=List[CartItemResponse], tags=["Shopping Cart"])
async def get_cart_items(user_id: int = 1, db: Session = Depends(get_db)):  # Hardcoded user_id for demo
    """Get cart items for a user using SQLAlchemy models from models.py"""
    cart_items = db.query(CartItemDB).filter(CartItemDB.user_id == user_id).all()
    
    # Manually construct response with product details
    response_items = []
    for item in cart_items:
        product = db.query(ProductDB).filter(ProductDB.id == item.product_id).first()
        if product:
            response_items.append({
                "id": item.id,
                "user_id": item.user_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "product": product,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            })
    
    return response_items

@router.post("/cart/add", response_model=CartItemResponse, tags=["Shopping Cart"])
async def add_to_cart(cart_item: CartItemCreate, user_id: int = 1, db: Session = Depends(get_db)):
    """Add item to cart using SQLAlchemy models from models.py"""
    # Check if product exists
    product = db.query(ProductDB).filter(ProductDB.id == cart_item.product_id, ProductDB.is_active == True).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {cart_item.product_id} not found"
        )
    
    # Check if item already in cart
    existing_item = db.query(CartItemDB).filter(
        CartItemDB.user_id == user_id,
        CartItemDB.product_id == cart_item.product_id
    ).first()
    
    if existing_item:
        # Update quantity
        existing_item.quantity += cart_item.quantity
        db.commit()
        db.refresh(existing_item)
        db_cart_item = existing_item
    else:
        # Create new cart item using SQLAlchemy model from models.py
        db_cart_item = CartItemDB(
            user_id=user_id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity
        )
        db.add(db_cart_item)
        db.commit()
        db.refresh(db_cart_item)
    
    # Return with product details
    return {
        "id": db_cart_item.id,
        "user_id": db_cart_item.user_id,
        "product_id": db_cart_item.product_id,
        "quantity": db_cart_item.quantity,
        "product": product,
        "created_at": db_cart_item.created_at,
        "updated_at": db_cart_item.updated_at
    }

@router.delete("/cart/{item_id}", tags=["Shopping Cart"])
async def remove_from_cart(item_id: int, user_id: int = 1, db: Session = Depends(get_db)):
    """Remove item from cart using SQLAlchemy models from models.py"""
    cart_item = db.query(CartItemDB).filter(
        CartItemDB.id == item_id,
        CartItemDB.user_id == user_id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart item with ID {item_id} not found"
        )
    
    db.delete(cart_item)
    db.commit()
    
    return {"message": f"Item removed from cart successfully"}

# --- Order Routes ---

@router.post("/orders", response_model=OrderResponse, tags=["Orders"])
async def create_order(order: OrderCreate, user_id: int = 1, db: Session = Depends(get_db)):
    """Create an order from cart items using SQLAlchemy models from models.py"""
    # Get user's cart items
    cart_items = db.query(CartItemDB).filter(CartItemDB.user_id == user_id).all()
    
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )
    
    # Calculate total amount
    total_amount = 0.0
    order_items_data = []
    
    for cart_item in cart_items:
        product = db.query(ProductDB).filter(ProductDB.id == cart_item.product_id).first()
        if product and product.stock_quantity >= cart_item.quantity:
            item_total = product.price * cart_item.quantity
            total_amount += item_total
            order_items_data.append({
                "product_id": product.id,
                "quantity": cart_item.quantity,
                "unit_price": product.price,
                "total_price": item_total
            })
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.name if product else cart_item.product_id}"
            )
    
    # Create order using SQLAlchemy model from models.py
    db_order = OrderDB(
        user_id=user_id,
        total_amount=total_amount,
        shipping_address=order.shipping_address,
        payment_info=order.payment_info,
        status=OrderStatus.PENDING.value
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Create order items
    for item_data in order_items_data:
        order_item = OrderItemDB(
            order_id=db_order.id,
            **item_data
        )
        db.add(order_item)
    
    # Clear cart and update product stock
    for cart_item in cart_items:
        product = db.query(ProductDB).filter(ProductDB.id == cart_item.product_id).first()
        if product:
            product.stock_quantity -= cart_item.quantity
        db.delete(cart_item)
    
    db.commit()
    
    return {
        "id": db_order.id,
        "user_id": db_order.user_id,
        "status": db_order.status,
        "total_amount": db_order.total_amount,
        "shipping_address": db_order.shipping_address,
        "payment_info": db_order.payment_info,
        "order_items": order_items_data,
        "created_at": db_order.created_at,
        "updated_at": db_order.updated_at
    }

@router.get("/orders", response_model=List[OrderResponse], tags=["Orders"])
async def get_orders(user_id: int = 1, db: Session = Depends(get_db)):
    """Get user's orders using SQLAlchemy models from models.py"""
    orders = db.query(OrderDB).filter(OrderDB.user_id == user_id).all()
    
    # Format response with order items
    response_orders = []
    for order in orders:
        order_items = db.query(OrderItemDB).filter(OrderItemDB.order_id == order.id).all()
        order_items_data = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price
            }
            for item in order_items
        ]
        
        response_orders.append({
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "payment_info": order.payment_info,
            "order_items": order_items_data,
            "created_at": order.created_at,
            "updated_at": order.updated_at
        })
    
    return response_orders