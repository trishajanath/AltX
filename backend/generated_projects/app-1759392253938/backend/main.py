# main.py
# To run this application:
# 1. Save this file as main.py
# 2. Save the second code block as routes.py in the same directory.
# 3. Install dependencies: pip install "fastapi[all]"
# 4. Run the server: uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import routes

# Create FastAPI app instance
app = FastAPI(
    title="app-1759392253938",
    description="A FastAPI application with CORS and a dedicated router.",
    version="1.0.0"
)

# CORS (Cross-Origin Resource Sharing) Middleware
# This allows web pages from any domain to make requests to this API.
# For production, you should restrict this to your frontend's domain.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include the router from routes.py with a prefix
app.include_router(routes.router, prefix="/api/v1")

# Health check endpoint at the root
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Provides a simple health check endpoint to confirm the service is running.
    """
    return {"status": "ok", "message": "Service is healthy"}

# Example of how to run the app (for development)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# routes.py
# This file should be in the same directory as main.py

from fastapi import APIRouter

# Create a new router object
router = APIRouter()

@router.get("/greet", tags=["Greetings"])
async def greet_user(name: str = "World"):
    """
    A simple greeting endpoint.
    Accepts an optional 'name' query parameter.
    """
    return {"message": f"Hello, {name} from app-1759392253938 API!"}

@router.get("/info", tags=["Application Info"])
async def get_app_info():
    """
    Returns basic information about the application.
    """
    return {
        "app_name": "app-1759392253938",
        "api_version": "v1",
        "status": "active"
    }

# You can add more routes to this router as your application grows.
# For example:
#
# from pydantic import BaseModel
#
# class Item(BaseModel):
#     name: str
#     price: float
#
# @router.post("/items", tags=["Items"])
# async def create_item(item: Item):
#     """
#     An example POST endpoint to create an item.
#     """
#     return {"status": "success", "item_received": item.dict()}