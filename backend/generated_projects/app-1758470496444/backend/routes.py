from fastapi import APIRouter, HTTPException, status, Body
from typing import List
from datetime import datetime

from . import models
from . import database as db

# Create an APIRouter instance. This helps in organizing routes.
# All routes defined here will be prefixed with what's specified in main.py.
router = APIRouter()

@router.get(
    "/tasks",
    response_model=List[models.Task],
    summary="Get All Tasks",
    description="Retrieve a list of all tasks from the in-memory database."
)
async def get_all_tasks():
    """
    Endpoint to retrieve all tasks.
    Returns a list of task objects.
    """
    return list(db.DB_TASKS.values())

@router.post(
    "/tasks",
    response_model=models.Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Task",
    description="Add a new task to the list."
)
async def create_task(task_create: models.TaskCreate):
    """
    Endpoint to create a new task.
    -   Accepts a `TaskCreate` model in the request body.
    -   Generates a new unique ID and creation timestamp.
    -   Adds the new task to the in-memory database.
    -   Returns the newly created task object with a 201 status code.
    """
    new_id = db.get_next_id()
    new_task = models.Task(
        id=new_id,
        created_at=datetime.utcnow(),
        **task_create.model_dump()  # Unpack fields from the input model
    )
    db.DB_TASKS[new_id] = new_task
    return new_task

@router.put(
    "/tasks/{task_id}",
    response_model=models.Task,
    summary="Update an Existing Task",
    description="Update a task's title, description, or completion status by its ID."
)
async def update_task(task_id: int, task_update: models.TaskUpdate):
    """
    Endpoint to update an existing task by its ID.
    -   If the task is not found, it raises a 404 Not Found error.
    -   It updates only the fields provided in the `TaskUpdate` request body.
    -   Returns the fully updated task object.
    """
    if task_id not in db.DB_TASKS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found")

    stored_task = db.DB_TASKS[task_id]
    
    # Use model_dump with exclude_unset=True to get only the fields
    # that were explicitly set in the request body.
    update_data = task_update.model_dump(exclude_unset=True)
    
    # Create an updated model by merging the stored data with the update data
    updated_task = stored_task.model_copy(update=update_data)
    
    db.DB_TASKS[task_id] = updated_task
    return updated_task

@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Task",
    description="Remove a task from the list by its ID."
)
async def delete_task(task_id: int):
    """
    Endpoint to delete a task by its ID.
    -   If the task is not found, it raises a 404 Not Found error.
    -   If deletion is successful, it returns a 204 No Content response,
        which is standard for successful DELETE operations with no body.
    """
    if task_id not in db.DB_TASKS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found")
    
    del db.DB_TASKS[task_id]
    # No return value needed for a 204 response
    return