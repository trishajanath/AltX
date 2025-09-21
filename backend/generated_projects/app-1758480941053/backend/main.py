from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="app-1758480941053 API",
    description="build a simple portfolio website ",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class HealthResponse(BaseModel):
    status: str
    message: str

class ItemCreate(BaseModel):
    name: str
    description: str

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: str

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to app-1758480941053 API"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="API is running successfully"
    )

@app.get("/api/items", response_model=list[ItemResponse])
async def get_items():
    # Mock data - replace with database queries
    return [
        ItemResponse(
            id=1,
            name="Sample Item",
            description="This is a sample item",
            created_at="2024-01-01T00:00:00Z"
        )
    ]

@app.post("/api/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    # Mock creation - replace with database insert
    return ItemResponse(
        id=2,
        name=item.name,
        description=item.description,
        created_at="2024-01-01T00:00:00Z"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)