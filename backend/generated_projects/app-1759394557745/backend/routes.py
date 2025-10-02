from fastapi import APIRouter, HTTPException, status, Response
from typing import List, Dict

# Assuming a models.py file exists in the same directory with the following content:
#
# from pydantic import BaseModel, Field
# from typing import Optional
#
# class TodoCreate(BaseModel):
#     title: str = Field(..., min_length=1, max_length=100)
#     description: Optional[str] = None
#
# class TodoUpdate(BaseModel):
#     title: Optional[str] = Field(None, min_length=1, max_length=100)
#     description: Optional[str] = None
#     completed: Optional[bool] = None
#
# class Todo(BaseModel):
#     id: int
#     title: str
#     description: Optional[str] = None
#     completed: bool = False
#
from .models import Todo, TodoCreate, TodoUpdate

# Create a router with a prefix for all routes
router = APIRouter(
    prefix="/api/v1",
    tags=["Todos"]
)

# In-memory storage for todos
# Using a dictionary for O(1) lookups by ID
db: Dict[int, Todo] = {
    1: Todo(id=1, title="Learn FastAPI", description="Study the official documentation."),
    2: Todo(id=2, title="Build a REST API", description="Use the knowledge to create an API.", completed=True),
    3: Todo(id=3, title="Deploy the App", description="Use Docker and a cloud provider.", completed=False),
}

# A simple counter to generate unique IDs for new todos
id_counter = len(db) + 1


@router.get("/todos", response_model=List[Todo])
async def get_all_todos():
    """
    Get all todo items.
    Returns a list of all todo items currently in the database.
    """
    return list(db.values())


@router.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
async def create_new_todo(todo_create: TodoCreate):
    """
    Create a new todo item.
    Accepts a title and an optional description, generates a unique ID,
    and adds the new todo to the database.
    """
    global id_counter
    new_todo = Todo(
        id=id_counter,
        title=todo_create.title,
        description=todo_create.description,
        completed=False
    )
    db[id_counter] = new_todo
    id_counter += 1
    return new_todo


@router.put("/todos/{todo_id}", response_model=Todo)
async def update_existing_todo(todo_id: int, todo_update: TodoUpdate):
    """
    Update an existing todo item.
    Finds a todo by its ID and updates its fields with the provided data.
    Raises a 404 error if the todo is not found.
    """
    if todo_id not in db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )

    stored_todo = db[todo_id]
    
    # Create a dictionary of the fields that are actually set in the request
    update_data = todo_update.model_dump(exclude_unset=True)
    
    # Create an updated model using the stored data and the new data
    updated_todo = stored_todo.model_copy(update=update_data)
    
    db[todo_id] = updated_todo
    return updated_todo


@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_a_todo(todo_id: int):
    """
    Delete a todo item.
    Removes a todo from the database by its ID.
    Raises a 404 error if the todo is not found.
    """
    if todo_id not in db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )
    
    del db[todo_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)