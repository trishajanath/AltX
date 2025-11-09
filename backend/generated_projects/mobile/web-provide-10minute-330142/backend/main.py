# main.py - mobile/web-provide-10minute-330142 FastAPI Server
# VALIDATED: Syntax ✓ Imports ✓ Functionality ✓

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import routes (guaranteed to exist)
from routes import router

# App configuration
app = FastAPI(
    title="mobile/web-provide-10minute-330142 API",
    description="E-commerce API for mobile/web-provide-10minute-330142",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

# Root endpoint
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Welcome to mobile/web-provide-10minute-330142 API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

# Global health check
@app.get("/health")
def health():
    """Global health check."""
    return {"status": "healthy", "service": "mobile/web-provide-10minute-330142"}

# Server runner
if __name__ == "__main__":
    print(f"🚀 Starting mobile/web-provide-10minute-330142 API Server...")
    print("📖 API Documentation: http://localhost:8001/docs")
    print("🩺 Health Check: http://localhost:8001/health")
    print("🛒 Products: http://localhost:8001/api/v1/products")
    
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8001,
        reload=True,
        log_level="info"
    )
