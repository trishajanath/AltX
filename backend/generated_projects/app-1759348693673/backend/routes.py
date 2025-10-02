from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas
from .database import get_db

api_router = APIRouter()

@api_router.post("/courses", response_model=schemas.Course, status_code=status.HTTP_201_CREATED, tags=["Courses"])
def create_new_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    """
    Create a new course.

    - **name**: Name of the course (must be unique).
    - **code**: Course code (must be unique).
    - **description**: Optional description of the course.
    """
    return crud.create_course(db=db, course=course)

@api_router.get("/courses", response_model=List[schemas.Course], tags=["Courses"])
def read_all_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of all courses with pagination.
    """
    courses = crud.get_courses(db, skip=skip, limit=limit)
    return courses