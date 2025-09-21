# routes.py
# API endpoints (routes) for the Todo application.

from fastapi import APIRouter, HTTPException, status, Body
from typing import List

from .models import Task, TaskCreate, TaskUpdate
from .database import DB

# Create an API router instance. This helps in modularizing the application.
# All routes defined here will be prefixed with what's specified in main.py.
router = APIRouter()

# 

# 
🛡️ SECURITY ADVISORY (IDOR - Insecure Direct Object Reference)
# This API does not implement authentication or authorization. As a result,
# any user can access, modify, or delete any task if they know its ID.
# In a production system, you MUST implement robust authentication (e.g., OAuth2)
# and authorization policies to ensure users can only access their own data.
# 

@router.get(
    "/tasks",
    response_model=List[Task],
    summary="Get all tasks",
    description="Retrieve a list of all tasks currently in the system.",
)
async def get_all_tasks():
    """
    Retrieve all tasks.
    """
    return list(DB.values())

@router.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Add a new task to the system. The task ID and creation timestamp are generated automatically.",
)
async def create_task(task_in: TaskCreate):
    """
    Create a new task.
    - Accepts a `TaskCreate` payload.
    - Creates a full `Task` object.
    - Stores it in the database.
    - Returns the newly created task.
    """
    # The Task model will automatically generate id and created_at
    new_task = Task(**task_in.model_dump())
    DB[new_task.id] = new_task
    return new_task

@router.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Get a single task by ID",
    description="Retrieve the details of a specific task by its unique ID.",
)
async def get_task_by_id(task_id: str):
    """
    Retrieve a single task by its ID.
    - Raises a 404 Not Found error if the task does not exist.
    """
    task = DB.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found."
        )
    return task

@router.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update a task",
    description="Update a task's title, description, or completion status. This endpoint handles marking a task as complete.",
)
async def update_task(task_id: str, task_update: TaskUpdate):
    """
    Update an existing task.
    - Uses `TaskUpdate` model, which has all optional fields.
    - Raises 404 if the task doesn't exist.
    - Updates only the fields provided in the request body.
    """
    task = DB.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found."
        )
    
    # Get the update data, excluding unset fields to avoid overwriting with None
    update_data = task_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No update data provided. At least one field (title, description, completed) must be present."
        )

    # Create a copy of the task object to update
    updated_task = task.model_copy(update=update_data)
    
    # Save the updated task back to the "database"
    DB[task_id] = updated_task
    
    return updated_task

@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Permanently delete a task from the system by its unique ID.",
)
async def delete_task(task_id: str):
    """
    Delete a task by its ID.
    - Raises 404 if the task doesn't exist.
    - Returns 204 No Content on successful deletion.
    """
    if task_id not in DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found."
        )
    
    del DB[task_id]
    # No body should be returned for a 204 response.
    return None