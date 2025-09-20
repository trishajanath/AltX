```python
from fastapi import APIRouter, HTTPException, status, Path
from typing import List, Dict

from . import models

# Create an API router instance. This helps in organizing endpoints.
# All routes defined here will be prefixed with what's set in main.py.
router = APIRouter()

# In-memory "database"
# In a real-world application, this would be replaced with a proper database
# like PostgreSQL, MySQL, or a NoSQL database like MongoDB.
# Using a dictionary for O(1) lookups, updates, and deletes.
db: Dict[int, models.Todo] = {}
id_counter = 0

@router.post(
    "/todos",
    response_model=models.Todo,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Todo",
    description="Adds a new todo item to the list.",
    tags=["Todos"]
)
def create_todo(todo_in: models.TodoCreate):
    """
    Creates a new todo item.

    - **title**: The title of the todo (required).
    - **description**: An optional description of the todo.
    """
    global id_counter
    id_counter += 1
    new_todo = models.Todo(
        id=id_counter,
        title=todo_in.title,
        description=todo_in.description,
        completed=False
    )
    db[id_counter] = new_todo
    return new_todo

@router.get(
    "/todos",
    response_model=List[models.Todo],
    summary="Get all Todos",
    description="Retrieves a list of all todo items.",
    tags=["Todos"]
)
def get_all_todos():
    """
    Returns a list of all todo items.
    """
    return list(db.values())

@router.get(
    "/todos/{todo_id}",
    response_model=models.Todo,
    summary="Get a specific Todo",
    description="Retrieves a single todo item by its ID.",
    tags=["Todos"]
)
def get_todo_by_id(todo_id: int = Path(..., title="The ID of the todo to retrieve", ge=1)):
    """
    Returns a single todo item if found.
    Raises a 404 error if the todo with the specified ID does not exist.
    """
    todo = db.get(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with ID {todo_id} not found")
    return todo

@router.put(
    "/todos/{todo_id}",
    response_model=models.Todo,
    summary="Update a Todo",
    description="Updates an existing todo item's title, description, or completion status.",
    tags=["Todos"]
)
def update_todo(todo_update: models.TodoUpdate, todo_id: int = Path(..., title="The ID of the todo to update", ge=1)):
    """
    Updates a todo item's attributes.

    - All fields in the request body are optional.
    - Raises a 404 error if the todo with the specified ID does not exist.
    """
    todo = db.get(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with ID {todo_id} not found")

    update_data = todo_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(todo, key, value)
    
    db[todo_id] = todo
    return todo

@router.delete(
    "/todos/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Todo",
    description="Deletes a todo item by its ID.",
    tags=["Todos"]
)
def delete_todo(todo_id: int = Path(..., title="The ID of the todo to delete", ge=1)):
    """
    Deletes a todo item.
    
    - Raises a 404 error if the todo with the specified ID does not exist.
    - Returns a 204 No Content response on successful deletion.
    """
    if todo_id not in db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with ID {todo_id} not found")
    del db[todo_id]
    # No response body for 204 status code
    return
```