# This file simulates a database using an in-memory dictionary.
# In a production application, this would be replaced with a real database connection
# (e.g., using SQLAlchemy with PostgreSQL or SQLite).

from datetime import datetime
from .models import Task

#  In-Memory Database 
# A simple dictionary to store our tasks. The key is the task ID.
# This data is ephemeral and will be lost when the server restarts.
DB_TASKS: dict[int, Task] = {}

#  Sample Data 
# Pre-populate the database with some realistic sample tasks for development and testing.
def initialize_db():
    """Initializes the in-memory database with sample data."""
    global DB_TASKS
    if not DB_TASKS:  # Only populate if the DB is empty
        sample_tasks = [
            Task(id=1, title="Setup FastAPI Project Structure", description="Create main.py, routes.py, models.py, and config.py.", completed=True, created_at=datetime.utcnow()),
            Task(id=2, title="Implement CRUD Endpoints", description="Create GET, POST, PUT, DELETE routes for tasks.", completed=True, created_at=datetime.utcnow()),
            Task(id=3, title="Build React Frontend", description="Use Vite and TypeScript to build the UI.", completed=False, created_at=datetime.utcnow()),
            Task(id=4, title="Connect Frontend to Backend API", description="Use axios or fetch to make API calls and manage state.", completed=False, created_at=datetime.utcnow()),
        ]
        DB_TASKS = {task.id: task for task in sample_tasks}

# A simple counter to generate unique IDs for new tasks.
# In a real database, this would be handled by the database's auto-increment feature.
TASK_ID_COUNTER = len(DB_TASKS)

def get_next_id() -> int:
    """Returns a new unique ID for a task."""
    global TASK_ID_COUNTER
    TASK_ID_COUNTER += 1
    return TASK_ID_COUNTER