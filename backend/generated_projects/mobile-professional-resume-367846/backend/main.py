# main.py
# To run this application:
# 1. Save this code as 'main.py'.
# 2. Save the second code block below as 'routes.py' in the same directory.
# 3. Install FastAPI and an ASGI server: pip install fastapi "uvicorn[standard]"
# 4. Run the server from your terminal: uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from routes.py
from routes import router as api_router

# Create the FastAPI app instance
app = FastAPI(
    title="Mobile Professional Resume API",
    description="API for the mobile-professional-resume-367846 project.",
    version="1.0.0"
)

# Define allowed origins for CORS.
# Using ["*"] allows all origins, which is convenient for development.
# For production, you should restrict this to your frontend's domain.
origins = [
    "*",
]

# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Health check endpoint at the root URL
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    A simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "API is running"}

# Include the router from routes.py with the specified prefix
app.include_router(api_router, prefix="/api/v1")

```

```python
# routes.py
# This file should be in the same directory as main.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

# Create an instance of APIRouter
router = APIRouter()

# --- Pydantic Models for Data Structure ---
# These models define the shape of your data and provide validation.

class ExperienceItem(BaseModel):
    title: str
    company: str
    period: str
    description: str

class EducationItem(BaseModel):
    institution: str
    degree: str
    period: str

class ResumeData(BaseModel):
    name: str
    title: str
    contact: dict
    experience: List[ExperienceItem]
    education: List[EducationItem]
    skills: List[str]

# --- Mock Database ---
# In a real application, this data would come from a database.
mock_resume_db = {
    "name": "Jane Doe",
    "title": "Senior Mobile & Backend Developer",
    "contact": {
        "email": "jane.doe@example.com",
        "phone": "123-456-7890",
        "linkedin": "linkedin.com/in/janedoe"
    },
    "experience": [
        {
            "title": "Senior Backend Engineer",
            "company": "Tech Solutions Inc.",
            "period": "2021 - Present",
            "description": "Led the development of scalable microservices using FastAPI and Docker. Integrated with mobile frontends."
        },
        {
            "title": "Mobile App Developer",
            "company": "MobileFirst Co.",
            "period": "2018 - 2021",
            "description": "Developed and maintained native iOS and Android applications for various clients."
        }
    ],
    "education": [
        {
            "institution": "University of Computing",
            "degree": "B.S. in Computer Science",
            "period": "2014 - 2018"
        }
    ],
    "skills": ["Python", "FastAPI", "Swift", "Kotlin", "Docker", "PostgreSQL", "REST APIs"]
}


# --- API Routes ---

@router.get("/", tags=["API Info"])
async def get_api_info():
    """
    Provides information about this API version.
    """
    return {"message": "Welcome to API Version 1 for the Professional Resume."}

@router.get("/resume", response_model=ResumeData, tags=["Resume"])
async def get_full_resume():
    """
    Retrieve the complete professional resume data.
    """
    return mock_resume_db

@router.get("/experience", response_model=List[ExperienceItem], tags=["Resume"])
async def get_experience():
    """
    Retrieve only the professional experience section of the resume.
    """
    return mock_resume_db["experience"]

@router.get("/education", response_model=List[EducationItem], tags=["Resume"])
async def get_education():
    """
    Retrieve only the education section of the resume.
    """
    return mock_resume_db["education"]