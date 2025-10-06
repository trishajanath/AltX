# main.py
# FastAPI application for e-portfolio-showcase-nilishas-041570

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

# --- In a real project, this APIRouter would be in a separate file like `api/routes.py` ---
api_router = APIRouter()

# Placeholder data for the e-portfolio
# In a real application, this would come from a database.
PROJECTS_DB = [
    {
        "id": 1,
        "title": "AI-Powered Personal Finance Manager",
        "description": "A web application that uses machine learning to categorize expenses and provide budget insights.",
        "technologies": ["Python", "FastAPI", "React", "Scikit-learn", "PostgreSQL"],
        "live_url": "https://example.com/finance-manager",
        "github_url": "https://github.com/nilishas-041570/finance-manager"
    },
    {
        "id": 2,
        "title": "E-commerce Recommendation Engine",
        "description": "Developed a collaborative filtering model to provide personalized product recommendations for an e-commerce platform.",
        "technologies": ["Python", "Pandas", "SurpriseLib", "Flask"],
        "live_url": None,
        "github_url": "https://github.com/nilishas-041570/recommendation-engine"
    },
    {
        "id": 3,
        "title": "Cloud-Based Data Pipeline",
        "description": "Designed and implemented an ETL pipeline on AWS to process and analyze real-time streaming data.",
        "technologies": ["AWS Lambda", "Kinesis", "S3", "Athena", "Terraform"],
        "live_url": None,
        "github_url": "https://github.com/nilishas-041570/data-pipeline"
    }
]

CONTACT_INFO = {
    "name": "Nilisha S.",
    "email": "contact@nilishas.dev",
    "linkedin": "https://linkedin.com/in/nilishas-example",
    "github": "https://github.com/nilishas-041570"
}

@api_router.get("/projects", response_model=List[Dict[str, Any]])
def get_projects():
    """
    Retrieve a list of all portfolio projects.
    """
    return PROJECTS_DB

@api_router.get("/projects/{project_id}", response_model=Dict[str, Any])
def get_project_by_id(project_id: int):
    """
    Retrieve a single project by its ID.
    """
    project = next((p for p in PROJECTS_DB if p["id"] == project_id), None)
    if not project:
        return {"error": "Project not found"}
    return project

@api_router.get("/contact", response_model=Dict[str, str])
def get_contact_info():
    """
    Retrieve contact information.
    """
    return CONTACT_INFO

# --- End of `routes.py` content ---


# Create the FastAPI app instance
app = FastAPI(
    title="E-Portfolio Showcase API",
    description="API for Nilisha's e-portfolio showcase (nilishas-041570).",
    version="1.0.0",
)

# Set up CORS (Cross-Origin Resource Sharing)
# This allows the frontend (running on a different domain) to communicate with this API.
origins = [
    "*",  # In production, you should restrict this to your frontend's domain
    # e.g., "https://your-frontend-domain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Health check endpoint
@app.get("/", tags=["Health Check"])
def read_root():
    """
    Root endpoint for health check.
    """
    return {"status": "ok", "message": "Welcome to the E-Portfolio Showcase API!"}


# Include the router from our simulated `routes.py` file
# All routes in `api_router` will be prefixed with `/api/v1`
app.include_router(api_router, prefix="/api/v1", tags=["Portfolio"])

# To run this application:
# 1. Install FastAPI and Uvicorn: pip install fastapi "uvicorn[standard]"
# 2. Save this code as `main.py`.
# 3. Run the server: uvicorn main:app --reload
# 4. Access the API docs at http://127.0.0.1:8000/docs