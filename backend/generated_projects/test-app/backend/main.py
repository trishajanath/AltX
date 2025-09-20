from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.main_routes import router as main_router

import uvicorn

app = FastAPI(
    title="Test App API",
    description="Backend API for test app",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(main_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Test App API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "test-app"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)