from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import date

# Import models from .models
# Note: The following models (Profile, Experience, Project) are assumed to be
# defined in a file named `models.py` in the same directory.
from .models import Profile, Experience, Project

# Create an APIRouter instance with a prefix for all routes in this file
router = APIRouter(
    prefix="/api/v1",
    tags=["Portfolio Data"],
)

# --- In-Memory Database ---
# This section acts as a mock database for demonstration purposes.

db_profile = {
    "name": "Jane Doe",
    "title": "Senior Software Engineer",
    "summary": "A passionate developer with over 10 years of experience in building scalable web applications and leading engineering teams. Specializing in Python, FastAPI, and cloud-native technologies.",
    "social_links": {
        "github": "https://github.com/janedoe",
        "linkedin": "https://linkedin.com/in/janedoe"
    }
}

db_experience = [
    {
        "id": 1,
        "title": "Senior Software Engineer",
        "company": "Tech Solutions Inc.",
        "start_date": date(2020, 1, 15),
        "end_date": None,
        "description": [
            "Led the development of a new microservices-based platform using FastAPI.",
            "Mentored junior developers and conducted code reviews.",
            "Improved application performance by 30% through query optimization."
        ]
    },
    {
        "id": 2,
        "title": "Software Engineer",
        "company": "Innovate Corp.",
        "start_date": date(2017, 6, 1),
        "end_date": date(2019, 12, 31),
        "description": [
            "Developed and maintained features for a large-scale Django application.",
            "Collaborated with product managers to define feature requirements.",
            "Wrote unit and integration tests to ensure code quality."
        ]
    },
    {
        "id": 3,
        "title": "Junior Developer",
        "company": "Startup Hub",
        "start_date": date(2015, 9, 1),
        "end_date": date(2017, 5, 30),
        "description": [
            "Assisted in the development of a customer-facing web portal.",
            "Fixed bugs and implemented small features.",
            "Gained experience with Python, Flask, and PostgreSQL."
        ]
    }
]

db_projects = [
    {
        "id": 1,
        "name": "Portfolio API",
        "description": "A RESTful API built with FastAPI to serve data for this portfolio website.",
        "tags": ["FastAPI", "Python", "API", "Pydantic"],
        "image_url": "https://example.com/images/project1.png",
        "project_url": "https://github.com/janedoe/portfolio-api",
        "display_order": 1
    },
    {
        "id": 2,
        "name": "E-commerce Analytics Dashboard",
        "description": "A data visualization dashboard using React and D3.js to display sales metrics.",
        "tags": ["React", "JavaScript", "D3.js", "Data Visualization"],
        "image_url": "https://example.com/images/project2.png",
        "project_url": "https://github.com/janedoe/analytics-dashboard",
        "display_order": 2
    },
    {
        "id": 3,
        "name": "Cloud File Processor",
        "description": "An AWS Lambda function to process uploaded files, resize images, and store them in S3.",
        "tags": ["AWS", "Lambda", "Python", "S3"],
        "image_url": "https://example.com/images/project3.png",
        "project_url": "https://github.com/janedoe/cloud-processor",
        "display_order": 3
    }
]


# --- API Endpoints ---

@router.get("/profile", response_model=Profile, summary="Retrieve main profile information")
async def get_profile():
    """
    Retrieve the main profile information (name, title, summary, social links).
    Example: Fetch data for the hero section.
    """
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile information not found")
    return db_profile


@router.get("/experience", response_model=List[Experience], summary="Retrieve all work experiences")
async def get_experience():
    """
    Retrieve a list of all work experiences, sorted by start date in descending order.
    Example: Populate the interactive timeline.
    """
    if not db_experience:
        return []
    # Sort experiences by start_date in descending order (most recent first)
    sorted_experience = sorted(db_experience, key=lambda x: x['start_date'], reverse=True)
    return sorted_experience


@router.get("/projects", response_model=List[Project], summary="Retrieve all portfolio projects")
async def get_projects():
    """
    Retrieve a list of all portfolio projects, sorted by display order.
    Example: Populate the project showcase grid.
    """
    if not db_projects:
        return []
    # Sort projects by the 'display_order' field
    sorted_projects = sorted(db_projects, key=lambda x: x['display_order'])
    return sorted_projects


@router.get("/projects/filter", response_model=List[Project], summary="Retrieve projects by technology tag")
async def get_filtered_projects(tag: str = Query(..., min_length=1, description="Technology tag to filter projects by")):
    """
    Retrieve projects filtered by a technology tag provided as a query parameter.
    The filter is case-insensitive.
    Example: GET /api/v1/projects/filter?tag=FastAPI
    """
    # Perform a case-insensitive search for the tag in each project's tags list
    filtered_projects = [
        project for project in db_projects
        if tag.lower() in [t.lower() for t in project['tags']]
    ]
    
    # Return the filtered list, sorted by display order for consistent results
    return sorted(filtered_projects, key=lambda x: x['display_order'])