```python
import uuid
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config import settings
from .routes import router as api_router, db as in_memory_db
from .models import Store, Product

#  Application Setup 
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="A modern, high-performance API for a quick delivery service.",
    # Disabling default docs URLs to use custom ones if needed
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

#  CORS (Cross-Origin Resource Sharing) Middleware 
# 💡 **Guidance:** This is a critical security feature for web applications.
# It tells browsers which web origins are allowed to access this API.
# The configuration below is secure for development with a React frontend
# running on localhost:5173. For production, you would replace this with
# your actual frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

#  Startup Event Handler 
@app.on_event("startup")
async def startup_event():
    """
    Populates the in-memory database with sample data on application startup.
    This makes the API immediately testable without needing to manually create data.
    """
    print("INFO:     Populating in-memory database with mock data...")
    # Create Products
    product1 = Product(name="Organic Bananas", price=1.29, stock_quantity=150)
    product2 = Product(name="Whole Milk, 1 Gallon", price=4.50, stock_quantity=80)
    product3 = Product(name="Artisan Sourdough Bread", price=5.99, stock_quantity=50)
    product4 = Product(name="Avocado", price=2.50, stock_quantity=200)

    # Create a Store and add inventory
    store1 = Store(
        name="Downtown Quick Mart",
        address="123 Main St, Anytown, USA",
        latitude=34.0522,
        longitude=-118.2437,
        inventory=[product1, product2, product3, product4]
    )
    in_memory_db["stores"][store1.id] = store1

    # Create another store
    product5 = Product(name="Cold Brew Coffee", price=4.75, stock_quantity=60)
    product6 = Product(name="Greek Yogurt", price=1.99, stock_quantity=120)
    store2 = Store(
        name="Uptown Grocers",
        address="456 Oak Ave, Anytown, USA",
        latitude=34.0600,
        longitude=-118.2500,
        inventory=[product5, product6, product1, product4] # Can have same products
    )
    in_memory_db["stores"][store2.id] = store2
    print("INFO:     Mock data populated.")

#  Custom Exception Handlers 
# 💡 **Guidance:** This ensures that your API returns consistent, well-formed
# JSON error responses instead of default server errors, which is crucial for
# frontend clients and for preventing information leakage.

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles Pydantic's validation errors to return a clean 422 response.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": exc.errors()},
    )

#  API Router Inclusion 
app.include_router(api_router, prefix=settings.API_V1_STR)

#  Root and Health Check Endpoints 
@app.get("/", tags=["Health Check"])
async def read_root():
    """A welcome message to confirm the API is running."""
    return {"message": f"Welcome to the {settings.APP_NAME}"}

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health Check"])
async def health_check():
    """
    Health check endpoint.
    Used by load balancers, container orchestrators (like Kubernetes), and monitoring
    tools to verify that the application is alive and operational.
    """
    return {"status": "ok"}

```