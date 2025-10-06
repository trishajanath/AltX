from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import date

# Assuming a 'models.py' file exists in the same directory with Pydantic models.
# To make this file runnable standalone, you would uncomment the model definitions
# in the 'models.py' file and place them here or in a separate file.
from .models import ProjectSummary, ProjectDetail, TimelineEvent, Profile

# --- In-Memory Data Store ---
# This acts as a mock database for the portfolio content.

db_projects: List[ProjectDetail] = [
    ProjectDetail(
        id=1,
        title="AI-Powered Personal Finance Dashboard",
        slug="ai-finance-dashboard",
        tagline="Smart financial insights using machine learning.",
        thumbnail_url="/images/thumbnails/finance-dashboard.jpg",
        tags=["Python", "FastAPI", "React", "Machine Learning"],
        description="A comprehensive dashboard that connects to users' bank accounts, categorizes transactions, and provides predictive insights on spending habits.",
        case_study="""
        ## The Challenge
        Users often struggle to understand their spending habits from raw bank statements. Our goal was to create an intuitive platform that not only visualizes data but also offers actionable advice.

        ## The Solution
        We built a secure REST API with FastAPI to handle data aggregation and a React frontend for visualization. A scikit-learn model was trained to categorize transactions with over 95% accuracy.
        """,
        live_url="https://example-finance.com",
        source_url="https://github.com/user/finance-dashboard",
        images=["/images/projects/finance-1.jpg", "/images/projects/finance-2.jpg"]
    ),
    ProjectDetail(
        id=2,
        title="E-commerce Platform for Artisans",
        slug="artisan-marketplace",
        tagline="Connecting local artisans with a global audience.",
        thumbnail_url="/images/thumbnails/artisan-marketplace.jpg",
        tags=["Django", "PostgreSQL", "Stripe", "Vue.js"],
        description="A full-featured e-commerce marketplace for artisans to sell their handmade goods. Includes inventory management, order processing, and secure payments via Stripe.",
        case_study="""
        ## Project Overview
        The primary objective was to empower small-scale creators by giving them a platform to reach a wider market. We focused on a simple, mobile-first user experience for both sellers and buyers.

        ## Technical Details
        The backend is a monolithic Django application with a PostgreSQL database. The frontend uses Vue.js for a reactive user interface. Stripe integration handles all payment processing securely.
        """,
        live_url="https://example-artisan.com",
        source_url=None,
        images=["/images/projects/artisan-1.jpg", "/images/projects/artisan-2.jpg"]
    ),
    ProjectDetail(
        id=3,
        title="Real-time Collaborative Whiteboard",
        slug="collaborative-whiteboard",
        tagline="Brainstorm with your team, wherever they are.",
        thumbnail_url="/images/thumbnails/whiteboard.jpg",
        tags=["Node.js", "WebSockets", "React", "Redis"],
        description="A web-based whiteboard application that allows multiple users to draw and share ideas in real-time.",
        case_study="""
        ## Real-time Communication
        The core of this project is its real-time capability, achieved using WebSockets. A Node.js server broadcasts drawing events to all connected clients. Redis is used to manage session state and message queuing.
        """,
        live_url="https://example-whiteboard.com",
        source_url="https://github.com/user/whiteboard-app",
        images=["/images/projects/whiteboard-1.jpg"]
    )
]

db_timeline: List[TimelineEvent] = [
    TimelineEvent(
        id=1,
        type="experience",
        title="Senior Software Engineer",
        organization="Tech Solutions Inc.",
        start_date=date(2021, 6, 1),
        end_date=None, # Present
        description="Leading the development of a new cloud-based analytics platform using Python, FastAPI, and Kubernetes. Mentoring junior developers and driving architectural decisions."
    ),
    TimelineEvent(
        id=2,
        type="experience",
        title="Software Engineer",
        organization="Innovatech",
        start_date=date(2018, 8, 15),
        end_date=date(2021, 5, 30),
        description="Developed and maintained features for a large-scale Django-based web application. Improved API performance by 30% through query optimization and caching strategies."
    ),
    TimelineEvent(
        id=3,
        type="education",
        title="Bachelor of Science in Computer Science",
        organization="State University",
        start_date=date(2014, 9, 1),
        end_date=date(2018, 5, 20),
        description="Graduated with honors. Focused on software engineering principles, algorithms, and database management. Completed a final year project on distributed systems."
    )
]

db_profile: Profile = Profile(
    name="Alex Doe",
    title="Senior Software Engineer",
    bio="A passionate and creative software engineer with over 5 years of experience in building scalable and efficient web applications. I thrive on solving complex problems and enjoy working in collaborative, fast-paced environments. My goal is to leverage technology to build products that make a difference.",
    profile_picture_url="/images/profile.jpg",
    skills=[
        "Python", "FastAPI", "Django", "JavaScript", "React",
        "SQL", "PostgreSQL", "Docker", "Kubernetes", "AWS"
    ],
    social_links={
        "linkedin": "https://linkedin.com/in/alexdoe",
        "github": "https://github.com/alexdoe",
        "twitter": "https://twitter.com/alexdoe"
    }
)


# --- API Router Setup ---

router = APIRouter(
    prefix="/api/v1",
    tags=["Portfolio API"]
)


# --- API Endpoints ---

@router.get(
    "/projects",
    response_model=List[ProjectSummary],
    summary="Get all projects",
    description="Retrieve a list of all projects with summary data for the main portfolio grid."
)
async def get_all_projects():
    """
    Returns a list of all projects.
    The data is returned in a summary format, suitable for a portfolio grid view.
    """
    return db_projects


@router.get(
    "/projects/{slug}",
    response_model=ProjectDetail,
    summary="Get a single project by slug",
    description="Retrieve the full details and case study content for a single project, identified by its unique slug."
)
async def get_project_by_slug(slug: str):
    """
    Finds and returns a single project by its unique slug.

    - **slug**: The URL-friendly identifier for the project.

    Raises a 404 Not Found error if no project with the given slug exists.
    """
    project = next((p for p in db_projects if p.slug == slug), None)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with slug '{slug}' not found"
        )
    return project


@router.get(
    "/timeline",
    response_model=List[TimelineEvent],
    summary="Get all timeline events",
    description="Retrieve all education and experience events, sorted chronologically, for building the timeline view."
)
async def get_timeline_events():
    """
    Returns a list of all education and work experience events.
    The list is sorted by start date in descending order (most recent first).
    """
    # Sort events by start_date, with the most recent first
    sorted_timeline = sorted(db_timeline, key=lambda x: x.start_date, reverse=True)
    return sorted_timeline


@router.get(
    "/profile",
    response_model=Profile,
    summary="Get profile information",
    description="Get general profile information for the 'About Me' page, such as bio, skills list, and profile picture URL."
)
async def get_profile_info():
    """
    Returns the main profile information for the portfolio.
    """
    return db_profile