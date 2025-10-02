from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException, status

def get_course_by_code(db: Session, course_code: str):
    return db.query(models.Course).filter(models.Course.code == course_code).first()

def get_courses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Course).offset(skip).limit(limit).all()

def create_course(db: Session, course: schemas.CourseCreate):
    # Check for uniqueness before creating
    db_course_by_code = get_course_by_code(db, course_code=course.code)
    if db_course_by_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Course with code '{course.code}' already exists."
        )
    
    db_course_by_name = db.query(models.Course).filter(models.Course.name == course.name).first()
    if db_course_by_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Course with name '{course.name}' already exists."
        )

    db_course = models.Course(**course.dict())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course