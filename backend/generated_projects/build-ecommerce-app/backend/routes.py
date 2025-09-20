```python
import uuid
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from models import (
    Product, Review, ReviewCreate, Order, OrderCreate,
    SentimentAnalysisResult, RecommendedProduct
)

#  Mock Database and AI Services (to be imported) 
# In a real application, these would be in separate files like `db.py` and `ai_services.py`

#  Mock Database 
# Using a simple dictionary to simulate a database.
mock_db: Dict[str, List] = {
    "products": [],
    "reviews": [],
    "orders": [],
    "user_interactions": [] # For recommendation engine
}

# Helper function to find an item by ID
def find_item_by_id(item_id: uuid.UUID, collection: str):
    for item in mock_db[collection]:
        if item.id == item_id:
            return item
    return None

#  Mock AI Services 
class MockAIServices:
    def analyze_sentiment(self, text: str) -> SentimentAnalysisResult:
        # Simple rule-based sentiment for mock purposes
        positive_words = ["good", "great", "excellent", "love", "amazing"]
        if any(word in text.lower() for word in positive_words):
            return SentimentAnalysisResult(label="POSITIVE", score=0.98)
        return SentimentAnalysisResult(label="NEGATIVE", score=0.95)

    def get_recommendations(self, user_id: int, num_recs: int) -> List[RecommendedProduct]:
        # Mock recommendations: return first few products user hasn't interacted with
        all_product_ids = {p.id for p in mock_db["products"]}
        interacted_ids = {i['product_id'] for i in mock_db["user_interactions"] if i['user_id'] == user_id}
        unseen_ids = list(all_product_ids - interacted_ids)

        recs = []
        for pid in unseen_ids[:num_recs]:
            product = find_item_by_id(pid, "products")
            if product:
                recs.append(RecommendedProduct(product=product, recommendation_score=0.85))
        return recs

# Dependency to provide the AI services
def get_ai_services():
    # In a real app, this would initialize and return real service instances
    return MockAIServices()

#  Pre-populate Mock Database 
def populate_db():
    if not mock_db["products"]:
        p1 = Product(name="Quantum Laptop", description="A laptop from the future.", price=1999.99, category="Electronics", stock=50)
        p2 = Product(name="The Art of Code", description="A book about writing beautiful code.", price=49.99, category="Books", stock=200)
        p3 = Product(name="Smart Hoodie", description="A hoodie that adjusts temperature.", price=129.50, category="Clothing", stock=150)
        mock_db["products"].extend([p1, p2, p3])
        r1 = Review(product_id=p1.id, rating=5, comment="This laptop is amazing! So fast.")
        r2 = Review(product_id=p1.id, rating=1, comment="Battery life is terrible.")
        mock_db["reviews"].extend([r1, r2])
        mock_db["user_interactions"].append({"user_id": 1, "product_id": p1.id})
populate_db()

#  API Router 
router = APIRouter()

#  Product Endpoints 
@router.get("/products", response_model=List[Product], tags=["Products"])
async def search_products(
    query: str = Query(None, min_length=3, description="Search query string"),
    category: str = Query(None, description="Filter by product category")
):
    """
    Search for products by name, description, and optionally filter by category.
    """
    results = mock_db["products"]
    if query:
        results = [p for p in results if query.lower() in p.name.lower() or query.lower() in p.description.lower()]
    if category:
        results = [p for p in results if p.category.value == category]
    return results

@router.get("/products/{product_id}", response_model=Product, tags=["Products"])
async def get_product_details(product_id: uuid.UUID = Path(..., description="The ID of the product to retrieve")):
    """
    Retrieve detailed information about a specific product.
    """
    product = find_item_by_id(product_id, "products")
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

#  Review Endpoints 
@router.post("/products/{product_id}/reviews", response_model=Review, status_code=status.HTTP_201_CREATED, tags=["Reviews"])
async def submit_review(
    product_id: uuid.UUID,
    review_data: ReviewCreate = Body(...)
):
    """
    Submit a new review for a product.
    """
    product = find_item_by_id(product_id, "products")
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cannot review a non-existent product")

    new_review = Review(product_id=product_id, **review_data.dict())
    mock_db["reviews"].append(new_review)
    return new_review

@router.get("/products/{product_id}/reviews", response_model=List[Review], tags=["Reviews"])
async def get_product_reviews(product_id: uuid.UUID):
    """
    Get all reviews for a specific product.
    """
    return [r for r in mock_db["reviews"] if r.product_id == product_id]

#  Order Endpoints 
@router.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED, tags=["Orders"])
async def create_new_order(order_data: OrderCreate):
    """
    Create a new order from a list of cart items.
    """
    total_price = 0
    for item in order_data.items:
        product = find_item_by_id(item.product_id, "products")
        if not product:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product with ID {item.product_id} not found.")
        if product.stock < item.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for {product.name}.")
        
        total_price += product.price * item.quantity
        product.stock -= item.quantity # Update stock

    new_order = Order(user_id=order_data.user_id, items=order_data.items, total_price=total_price)
    mock_db["orders"].append(new_order)
    return new_order

#  AI-Powered Endpoints 
@router.get("/recommendations/{user_id}", response_model=List[RecommendedProduct], tags=["AI Features"])
async def get_personalized_recommendations(
    user_id: int,
    ai_services: MockAIServices = Depends(get_ai_services)
):
    """
    [AI] Get personalized product recommendations for a given user ID.
    """
    recommendations = ai_services.get_recommendations(user_id, num_recs=5)
    if not recommendations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recommendations available for this user.")
    return recommendations

@router.get("/reviews/{review_id}/sentiment", response_model=SentimentAnalysisResult, tags=["AI Features"])
async def analyze_review_sentiment(
    review_id: uuid.UUID,
    ai_services: MockAIServices = Depends(get_ai_services)
):
    """
    [AI] Analyze the sentiment of a specific product review.
    """
    review = find_item_by_id(review_id, "reviews")
    if not review or not review.comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found or has no text content to analyze.")
    
    return ai_services.analyze_sentiment(review.comment)
```