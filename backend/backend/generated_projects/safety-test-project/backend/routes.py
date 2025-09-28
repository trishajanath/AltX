from typing import List
from fastapi import APIRouter, HTTPException, status
from models import Task, TaskCreate, TaskUpdate

router = APIRouter()

# In-memory storage fallback
_tasks: List[Task] = []

@router.get('/api/tasks', response_model=List[Task])
def list_tasks() -> List[Task]:
    return _tasks

@router.post('/api/tasks', response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    task = Task(**payload.dict())
    _tasks.append(task)
    return task

@router.get('/api/tasks/{task_id}', response_model=Task)
def get_task(task_id: str) -> Task:
    for t in _tasks:
        if t.id == task_id:
            return t
    raise HTTPException(status_code=404, detail='Task not found')

@router.put('/api/tasks/{task_id}', response_model=Task)
def update_task(task_id: str, payload: TaskUpdate) -> Task:
    for i, t in enumerate(_tasks):
        if t.id == task_id:
            updated = t.copy(update=payload.dict(exclude_unset=True))
            _tasks[i] = updated
            return updated
    raise HTTPException(status_code=404, detail='Task not found')

@router.delete('/api/tasks/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str) -> None:
    global _tasks
    _tasks = [t for t in _tasks if t.id != task_id]
    return None
