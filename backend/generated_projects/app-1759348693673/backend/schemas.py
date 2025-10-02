from pydantic import BaseModel, Field
from typing import Optional

# Shared properties
class CourseBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, example="Introduction to Computer Science")
    code: str = Field(..., min_length=3, max_length=20, example="CS101")
    description: Optional[str] = Field(None, example="A foundational course on programming and computer science principles.")

# Properties to receive on item creation
class CourseCreate(CourseBase):
    pass

# Properties to receive on item update
class CourseUpdate(CourseBase):
    pass

# Properties to return to client
class Course(CourseBase):
    id: int

    class Config:
        orm_mode = True